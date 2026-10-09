"""Claude provider — read-only reuse of Claude Code credentials."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from . import ProviderError
from .contract import project_ok

DEFAULT_CREDENTIALS = Path.home() / ".claude" / ".credentials.json"
DEFAULT_API_BASE = "https://api.anthropic.com"
USAGE_PATH = "/api/oauth/usage"
OAUTH_BETA = "oauth-2025-04-20"

# Claude Code /usage titles (CLI 2.1.295). Order matches that dialog.
_WINDOW_LABELS = {
    "five_hour": "Current session",
    "seven_day": "Current week (all models)",
    "seven_day_opus": "Opus limit",
    "seven_day_sonnet": "Current week (Sonnet only)",
    "seven_day_oauth_apps": "OAuth apps limit",
    "seven_day_cowork": "Cowork limit",
    "seven_day_omelette": "Omelette limit",
    "seven_day_overage_included": "Fable limit",
}
_WINDOW_ORDER = list(_WINDOW_LABELS)
# Present on the usage payload but not remaining-quota meters.
_NON_WINDOW_KEYS = {
    "extra_usage",
    "limits",
    "spend",
    "member_dashboard_available",
    "seven_day_breakdown",
    "weekly_scoped_shares",
}
_PLAN_LABELS = {
    "pro": "Pro",
    "max": "Max",
    "team": "Team",
    "enterprise": "Enterprise",
}


class ClaudeProvider:
    id = "claude"
    display_name = "Claude"

    def __init__(self, credentials_path: Path | None = None):
        env = os.environ.get("CLAUDE_CREDENTIALS_FILE")
        if credentials_path is not None:
            self.credentials_path = Path(credentials_path)
        elif env:
            self.credentials_path = Path(env).expanduser()
        else:
            self.credentials_path = DEFAULT_CREDENTIALS
        self.api_base = os.environ.get("CLAUDE_API_BASE", DEFAULT_API_BASE).rstrip("/")

    def detect(self) -> None:
        if not self.credentials_path.is_file():
            raise ProviderError(
                "auth_unavailable",
                "Claude Code credentials not found. Re-authenticate in Claude Code.",
            )

    def fetch_usage(self, *, force_refresh: bool = False) -> dict[str, Any]:
        # force_refresh must not refresh or rewrite Claude Code credentials.
        del force_refresh
        self.detect()
        oauth = self._read_oauth()
        usage = self._get_usage(str(oauth["accessToken"]))
        return self._normalize(usage, _plan_label(oauth.get("subscriptionType")))

    def _read_oauth(self) -> dict[str, Any]:
        try:
            fd = os.open(self.credentials_path, os.O_RDONLY)
        except OSError as exc:
            raise ProviderError(
                "auth_unavailable",
                "Cannot read Claude Code credentials. Re-authenticate in Claude Code.",
            ) from exc
        try:
            with os.fdopen(fd, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "auth_unavailable",
                "Claude Code credentials file is not valid JSON. Re-authenticate in Claude Code.",
            ) from exc
        except OSError as exc:
            raise ProviderError(
                "auth_unavailable",
                "Cannot read Claude Code credentials. Re-authenticate in Claude Code.",
            ) from exc

        if not isinstance(data, dict):
            raise ProviderError(
                "auth_unavailable",
                "Claude Code credentials file is not valid JSON. Re-authenticate in Claude Code.",
            )
        oauth = data.get("claudeAiOauth")
        if not isinstance(oauth, dict):
            raise ProviderError(
                "auth_unavailable",
                "Claude Code OAuth session not found. Re-authenticate in Claude Code.",
            )
        token = oauth.get("accessToken")
        if not isinstance(token, str) or not token.strip():
            raise ProviderError(
                "auth_unavailable",
                "Claude Code access token not found. Re-authenticate in Claude Code.",
            )
        if _expired(oauth.get("expiresAt")):
            raise ProviderError(
                "auth_unavailable",
                "Claude Code session expired. Re-authenticate in Claude Code.",
            )
        return oauth

    def _get_usage(self, access_token: str) -> dict[str, Any]:
        url = self.api_base + USAGE_PATH
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("anthropic-beta", OAUTH_BETA)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "horizon-ai-usage")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in (401, 403):
                raise ProviderError(
                    "auth_unavailable",
                    f"Claude usage unauthorized (HTTP {status}). Re-authenticate in Claude Code.",
                ) from exc
            raise ProviderError("upstream_error", f"Claude usage failed (HTTP {status})") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("upstream_error", f"Claude network error: {exc.reason}") from exc

        if status != 200:
            raise ProviderError("upstream_error", f"Claude usage failed (HTTP {status})")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderError("upstream_error", "Claude usage response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderError("upstream_error", "Claude usage response had unexpected shape")
        return data

    def _normalize(self, usage: dict[str, Any], plan_label: str) -> dict[str, Any]:
        windows = _quota_windows(usage)
        if not windows:
            raise ProviderError("upstream_error", "Claude usage response had no utilization windows")

        breakdown: list[dict[str, Any]] = []
        for key, window in windows:
            remaining = _remaining_from_used(_utilization(window))
            if remaining is None:
                continue
            line: dict[str, Any] = {
                "label": _label_for(key, window),
                "remainingPercent": remaining,
            }
            reset_at = _reset_at(window)
            if reset_at:
                line["resetAt"] = reset_at
            breakdown.append(line)

        if not breakdown:
            raise ProviderError("upstream_error", "Claude usage response had no utilization windows")

        return project_ok(
            provider=self.id,
            display_name=self.display_name,
            plan=plan_label,
            meters=breakdown,
        )


def _plan_label(subscription_type: Any) -> str:
    if not isinstance(subscription_type, str):
        return "Claude"
    key = subscription_type.strip().lower()
    if key in _PLAN_LABELS:
        return _PLAN_LABELS[key]
    if key.isalnum() and len(key) <= 24:
        return key[:1].upper() + key[1:]
    return "Claude"


def _expired(expires_at: Any) -> bool:
    if expires_at is None:
        return False
    try:
        stamp = float(expires_at)
    except (TypeError, ValueError):
        return False
    # Claude Code stores unix milliseconds. Values below 1e11 are seconds.
    if stamp < 100_000_000_000:
        stamp *= 1000.0
    return stamp <= time.time() * 1000.0


def _utilization(window: dict[str, Any]) -> float | None:
    value = window.get("utilization")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _remaining_from_used(used: float | None) -> int | None:
    if used is None:
        return None
    return max(0, min(100, int(round(100.0 - used))))


def _reset_at(window: dict[str, Any]) -> str | None:
    raw = window.get("resets_at")
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text or len(text) > 40:
        return None
    return text


def _label_for(key: str, window: dict[str, Any]) -> str:
    if key == "extra_usage":
        return "Extra usage"
    known = _WINDOW_LABELS.get(key)
    if known:
        return known
    raw = window.get("label")
    if isinstance(raw, str) and raw.strip() and len(raw.strip()) <= 40:
        return raw.strip()
    return key.replace("_", " ").strip().title() or "Claude"


def _quota_windows(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for key in _WINDOW_ORDER:
        window = payload.get(key)
        if isinstance(window, dict) and _utilization(window) is not None:
            found.append((key, window))
            seen.add(key)
    for key, window in payload.items():
        if key in seen or key in _NON_WINDOW_KEYS:
            continue
        if isinstance(window, dict) and _utilization(window) is not None:
            found.append((key, window))
    extra = payload.get("extra_usage")
    if (
        isinstance(extra, dict)
        and extra.get("is_enabled") is True
        and _utilization(extra) is not None
    ):
        found.append(("extra_usage", extra))
    return found
