"""Cursor provider — read-only reuse of Cursor IDE state.vscdb / CLI auth.json + DashboardService."""

from __future__ import annotations

import json
import math
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ProviderError
from .contract import project_ok

DEFAULT_STATE_DB = (
    Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "state.vscdb"
)
DEFAULT_CLI_AUTH = Path.home() / ".config" / "cursor" / "auth.json"
DEFAULT_API_BASE = "https://api2.cursor.sh"
USAGE_PATH = "/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
PLAN_PATH = "/aiserver.v1.DashboardService/GetPlanInfo"


class _AuthRejectedError(Exception):
    """Internal marker for HTTP 401/403 from DashboardService (carries no token)."""

    def __init__(self, status: int) -> None:
        super().__init__(f"rejected (HTTP {status})")
        self.status = status


def _is_jwt_shaped(value: Any) -> bool:
    """Shape check only: non-empty str with exactly three non-empty dot-separated parts."""
    if not isinstance(value, str) or not value:
        return False
    parts = value.split(".")
    return len(parts) == 3 and all(bool(part) for part in parts)


def _auth_failure_message(ide_outcome: str, cli_outcome: str) -> str:
    return (
        f"Cursor usage unauthorized: IDE {ide_outcome}; CLI {cli_outcome}. "
        "Sign in to Cursor or the Cursor CLI (agent login)."
    )


class CursorProvider:
    id = "cursor"
    display_name = "Cursor"

    def __init__(self, state_db: Path | None = None, cli_auth: Path | None = None):
        env = os.environ.get("CURSOR_STATE_VSCDB")
        if state_db is not None:
            self.state_db = Path(state_db)
        elif env:
            self.state_db = Path(env).expanduser()
        else:
            self.state_db = DEFAULT_STATE_DB

        cli_env = os.environ.get("CURSOR_CLI_AUTH_FILE")
        if cli_auth is not None:
            self.cli_auth = Path(cli_auth)
        elif cli_env:
            self.cli_auth = Path(cli_env).expanduser()
        else:
            self.cli_auth = DEFAULT_CLI_AUTH

        # Test/override hook only; production uses DEFAULT_API_BASE.
        self.api_base = os.environ.get("CURSOR_API_BASE", DEFAULT_API_BASE).rstrip("/")

    def detect(self) -> None:
        if not self.state_db.is_file() and not self.cli_auth.is_file():
            raise ProviderError(
                "auth_unavailable",
                _auth_failure_message("not found", "not found"),
            )

    def fetch_usage(self, *, force_refresh: bool = False) -> dict[str, Any]:
        del force_refresh  # Cursor tokens are not refreshed/written by Horizon (read-only).
        self.detect()

        ide_token, ide_outcome, membership = self._read_ide_candidate()
        usage: dict[str, Any] | None = None
        winning_token: str | None = None

        if ide_token is not None:
            try:
                usage = self._post_json(self.api_base + USAGE_PATH, ide_token, {})
                winning_token = ide_token
            except _AuthRejectedError as exc:
                ide_outcome = f"rejected (HTTP {exc.status})"

        if usage is None:
            cli_token, cli_outcome = self._read_cli_candidate()
            if cli_token is not None:
                try:
                    usage = self._post_json(self.api_base + USAGE_PATH, cli_token, {})
                    winning_token = cli_token
                except _AuthRejectedError as exc:
                    cli_outcome = f"rejected (HTTP {exc.status})"
            if usage is None:
                raise ProviderError(
                    "auth_unavailable",
                    _auth_failure_message(
                        ide_outcome or "no token",
                        cli_outcome or "no token",
                    ),
                )

        assert winning_token is not None
        plan_label = self._plan_label(membership, winning_token)
        return self._normalize(usage, plan_label)

    def _read_ide_candidate(self) -> tuple[str | None, str | None, str | None]:
        if not self.state_db.is_file():
            return None, "not found", None
        try:
            con = sqlite3.connect(f"file:{self.state_db}?mode=ro", uri=True)
        except (sqlite3.Error, OSError):
            return None, "unreadable", None
        try:
            cur = con.cursor()
            row = cur.execute(
                "SELECT value FROM ItemTable WHERE key = ?",
                ("cursorAuth/accessToken",),
            ).fetchone()
            mem = cur.execute(
                "SELECT value FROM ItemTable WHERE key = ?",
                ("cursorAuth/stripeMembershipType",),
            ).fetchone()
            membership = str(mem[0]) if mem and isinstance(mem[0], str) and mem[0] else None
        except (sqlite3.Error, OSError):
            return None, "unreadable", None
        finally:
            con.close()

        if not row or not isinstance(row[0], str) or not row[0].strip():
            return None, "no token", membership
        raw_token = row[0].strip()
        if not _is_jwt_shaped(raw_token):
            return None, "unsupported format", membership
        return raw_token, None, membership

    def _read_cli_candidate(self) -> tuple[str | None, str | None]:
        if not self.cli_auth.is_file():
            return None, "not found"
        try:
            with self.cli_auth.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None, "unreadable"
        if not isinstance(data, dict):
            return None, "unreadable"
        token = data.get("accessToken")
        if not isinstance(token, str) or not token.strip():
            return None, "no token"
        return token.strip(), None

    def _post_json(self, url: str, access_token: str, body: dict[str, Any]) -> dict[str, Any]:
        raw_body = json.dumps(body).encode()
        req = urllib.request.Request(url, data=raw_body, method="POST")
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("Connect-Protocol-Version", "1")
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in (401, 403):
                raise _AuthRejectedError(status) from exc
            raise ProviderError("upstream_error", f"Cursor usage failed (HTTP {status})") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("upstream_error", f"Cursor network error: {exc.reason}") from exc

        if status != 200:
            raise ProviderError("upstream_error", f"Cursor usage failed (HTTP {status})")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ProviderError("upstream_error", "Cursor usage response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderError("upstream_error", "Cursor usage response had unexpected shape")
        return data

    def _plan_label(self, membership: str | None, access_token: str) -> str:
        # Prefer live plan info; fall back to local membership type.
        try:
            info = self._post_json(self.api_base + PLAN_PATH, access_token, {})
            plan_info = info.get("planInfo") or {}
            name = plan_info.get("planName")
            if isinstance(name, str) and name.strip():
                return name.strip()
        except (ProviderError, _AuthRejectedError):
            pass
        if membership:
            return membership[:1].upper() + membership[1:]
        return "Cursor"

    @staticmethod
    def _clamp_pct(value: float) -> int:
        return max(0, min(100, int(round(value))))

    @staticmethod
    def _remaining_from_used_percent(used: Any) -> int | None:
        if used is None or isinstance(used, bool):
            return None
        try:
            used_val = float(used)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(used_val):
            return None
        return CursorProvider._clamp_pct(100.0 - used_val)

    def _normalize(self, usage: dict[str, Any], plan_label: str) -> dict[str, Any]:
        plan_usage = usage.get("planUsage") or {}
        if not isinstance(plan_usage, dict):
            plan_usage = {}

        # Live Cursor Usage UI exposes two pools only:
        # - Cursor Models ← autoPercentUsed (first-party / auto bucket)
        # - Other Models  ← apiPercentUsed (named / third-party API bucket)
        # Do not map remaining/limit/totalSpend/displayMessage/"included" aggregate as a meter.
        cursor_models = self._remaining_from_used_percent(plan_usage.get("autoPercentUsed"))
        other_models = self._remaining_from_used_percent(plan_usage.get("apiPercentUsed"))
        if cursor_models is None and other_models is None:
            raise ProviderError(
                "upstream_error",
                "Cursor usage missing autoPercentUsed/apiPercentUsed",
            )

        reset_at = None
        end_ms = usage.get("billingCycleEnd")
        if end_ms is not None:
            try:
                epoch = int(str(end_ms)) / 1000.0
                reset_at = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone().isoformat()
            except (TypeError, ValueError, OSError):
                reset_at = None

        breakdown: list[dict[str, Any]] = []
        if cursor_models is not None:
            line: dict[str, Any] = {
                "label": "Cursor Models",
                "remainingPercent": cursor_models,
            }
            if reset_at:
                line["resetAt"] = reset_at
            breakdown.append(line)
        if other_models is not None:
            line = {
                "label": "Other Models",
                "remainingPercent": other_models,
            }
            if reset_at:
                line["resetAt"] = reset_at
            breakdown.append(line)

        return project_ok(
            provider=self.id,
            display_name=self.display_name,
            plan=plan_label,
            meters=breakdown,
        )
