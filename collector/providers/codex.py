"""Codex provider — ChatGPT OAuth via ~/.codex/auth.json + wham/usage."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ProviderError

CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
REFRESH_URL = os.environ.get(
    "CODEX_REFRESH_TOKEN_URL_OVERRIDE", "https://auth.openai.com/oauth/token"
)
USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
DEFAULT_AUTH = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "auth.json"

PLAN_LABELS = {
    "plus": "ChatGPT Plus",
    "pro": "ChatGPT Pro",
    "free": "ChatGPT Free",
    "team": "ChatGPT Team",
}


class CodexProvider:
    id = "codex"
    display_name = "Codex"

    def __init__(self, auth_path: Path | None = None):
        self.auth_path = Path(auth_path) if auth_path else DEFAULT_AUTH

    def detect(self) -> None:
        if not self.auth_path.is_file():
            raise ProviderError("auth_unavailable", f"Codex auth file not found: {self.auth_path}")

    def fetch_usage(self, *, force_refresh: bool = False) -> dict[str, Any]:
        self.detect()
        auth = self._load_auth()
        tokens = auth.get("tokens") or {}
        if not isinstance(tokens, dict) or not tokens.get("access_token"):
            if tokens.get("refresh_token"):
                auth = self._refresh_tokens(auth)
                tokens = auth.get("tokens") or {}
            else:
                raise ProviderError("auth_unavailable", "Codex ChatGPT tokens are missing")

        if force_refresh:
            auth = self._refresh_tokens(auth)
            tokens = auth.get("tokens") or {}

        access = tokens.get("access_token")
        account_id = tokens.get("account_id")
        if not access:
            raise ProviderError("auth_unavailable", "Codex access_token missing after refresh")

        try:
            usage = self._fetch_usage(access, account_id if isinstance(account_id, str) else None)
        except ProviderError as exc:
            if exc.code == "auth_unavailable" and tokens.get("refresh_token") and not force_refresh:
                auth = self._refresh_tokens(auth)
                tokens = auth.get("tokens") or {}
                access = tokens.get("access_token")
                if not access:
                    raise ProviderError("auth_unavailable", "Refresh did not yield access_token") from exc
                aid = tokens.get("account_id")
                usage = self._fetch_usage(access, aid if isinstance(aid, str) else None)
            else:
                raise

        return self._normalize(usage)

    def _load_auth(self) -> dict[str, Any]:
        try:
            data = json.loads(self.auth_path.read_text())
        except json.JSONDecodeError as exc:
            raise ProviderError("auth_unavailable", f"Codex auth file is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ProviderError("auth_unavailable", "Codex auth file has unexpected shape")
        return data

    def _save_auth(self, data: dict[str, Any]) -> None:
        self.auth_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".auth-", suffix=".tmp", dir=str(self.auth_path.parent))
        try:
            with os.fdopen(fd, "w") as tmp:
                json.dump(data, tmp, indent=2)
                tmp.write("\n")
            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, self.auth_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def _refresh_tokens(self, auth: dict[str, Any]) -> dict[str, Any]:
        tokens = auth.get("tokens") or {}
        refresh = tokens.get("refresh_token")
        if not refresh:
            raise ProviderError("auth_unavailable", "No refresh_token in Codex auth")

        body = json.dumps(
            {
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh,
            }
        ).encode()
        req = urllib.request.Request(REFRESH_URL, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 401, 403):
                raise ProviderError(
                    "auth_unavailable",
                    f"Codex token refresh failed (HTTP {exc.code})",
                ) from exc
            raise ProviderError("upstream_error", f"Token refresh upstream error (HTTP {exc.code})") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("upstream_error", f"Token refresh network error: {exc.reason}") from exc

        if not isinstance(payload, dict) or not payload.get("access_token"):
            raise ProviderError("upstream_error", "Token refresh returned unexpected payload")

        new_tokens = dict(tokens)
        new_tokens["access_token"] = payload["access_token"]
        if payload.get("refresh_token"):
            new_tokens["refresh_token"] = payload["refresh_token"]
        if payload.get("id_token"):
            new_tokens["id_token"] = payload["id_token"]
        auth = dict(auth)
        auth["tokens"] = new_tokens
        auth["last_refresh"] = datetime.now(timezone.utc).isoformat()
        self._save_auth(auth)
        return auth

    def _fetch_usage(self, access_token: str, account_id: str | None) -> dict[str, Any]:
        req = urllib.request.Request(USAGE_URL, method="GET")
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Accept", "application/json")
        req.add_header("Referer", "https://chatgpt.com/codex/settings/usage")
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        )
        if account_id:
            req.add_header("ChatGPT-Account-ID", account_id)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in (401, 403):
                raise ProviderError("auth_unavailable", f"Usage request unauthorized (HTTP {status})") from exc
            raise ProviderError("upstream_error", f"Usage request failed (HTTP {status})") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("upstream_error", f"Usage network error: {exc.reason}") from exc

        if status != 200:
            raise ProviderError("upstream_error", f"Usage request failed (HTTP {status})")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderError("upstream_error", "Usage response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderError("upstream_error", "Usage response had unexpected shape")
        return data

    def _normalize(self, usage: dict[str, Any]) -> dict[str, Any]:
        plan_type = usage.get("plan_type") or "unknown"
        plan = PLAN_LABELS.get(str(plan_type).lower(), str(plan_type))

        rate = usage.get("rate_limit") or {}
        window = rate.get("primary_window") or usage.get("primary_window") or {}
        if not isinstance(window, dict):
            window = {}

        used = window.get("used_percent")
        if used is None:
            raise ProviderError("upstream_error", "Usage response missing primary used_percent")
        try:
            used_f = float(used)
        except (TypeError, ValueError) as exc:
            raise ProviderError("upstream_error", "used_percent is not numeric") from exc

        remaining = max(0, min(100, int(round(100 - used_f))))

        reset_at = None
        if window.get("reset_at") is not None:
            try:
                epoch = int(window["reset_at"])
                reset_at = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone().isoformat()
            except (TypeError, ValueError, OSError):
                reset_at = None
        elif window.get("reset_after_seconds") is not None:
            try:
                secs = int(window["reset_after_seconds"])
                now = datetime.now(timezone.utc).timestamp()
                reset_at = datetime.fromtimestamp(now + secs, tz=timezone.utc).astimezone().isoformat()
            except (TypeError, ValueError, OSError):
                reset_at = None

        out: dict[str, Any] = {
            "provider": self.id,
            "displayName": self.display_name,
            "plan": plan,
            "remainingPercent": remaining,
            "resetAt": reset_at,
            "status": "ok",
        }
        secondary = rate.get("secondary_window")
        if isinstance(secondary, dict) and secondary.get("used_percent") is not None:
            try:
                sec_used = float(secondary["used_percent"])
                out["secondaryRemainingPercent"] = max(0, min(100, int(round(100 - sec_used))))
            except (TypeError, ValueError):
                pass
        return out
