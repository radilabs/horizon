"""Cursor provider — read-only reuse of Cursor IDE state.vscdb + DashboardService."""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ProviderError

DEFAULT_STATE_DB = (
    Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "state.vscdb"
)
DEFAULT_API_BASE = "https://api2.cursor.sh"
USAGE_PATH = "/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
PLAN_PATH = "/aiserver.v1.DashboardService/GetPlanInfo"


class CursorProvider:
    id = "cursor"
    display_name = "Cursor"

    def __init__(self, state_db: Path | None = None):
        env = os.environ.get("CURSOR_STATE_VSCDB")
        if state_db is not None:
            self.state_db = Path(state_db)
        elif env:
            self.state_db = Path(env).expanduser()
        else:
            self.state_db = DEFAULT_STATE_DB
        # Test/override hook only; production uses DEFAULT_API_BASE.
        self.api_base = os.environ.get("CURSOR_API_BASE", DEFAULT_API_BASE).rstrip("/")

    def detect(self) -> None:
        if not self.state_db.is_file():
            raise ProviderError(
                "auth_unavailable",
                f"Cursor state database not found: {self.state_db}",
            )

    def fetch_usage(self, *, force_refresh: bool = False) -> dict[str, Any]:
        del force_refresh  # Cursor tokens are not refreshed/written by Horizon (read-only).
        self.detect()
        access_token, membership = self._read_auth_meta()
        usage = self._post_json(self.api_base + USAGE_PATH, access_token, {})
        plan_label = self._plan_label(membership, access_token)
        return self._normalize(usage, plan_label)

    def _read_auth_meta(self) -> tuple[str, str | None]:
        try:
            con = sqlite3.connect(f"file:{self.state_db}?mode=ro", uri=True)
        except sqlite3.Error as exc:
            raise ProviderError("auth_unavailable", f"Cannot open Cursor state DB: {exc}") from exc
        try:
            cur = con.cursor()
            row = cur.execute(
                "SELECT value FROM ItemTable WHERE key = ?",
                ("cursorAuth/accessToken",),
            ).fetchone()
            if not row or not row[0]:
                raise ProviderError("auth_unavailable", "Cursor access token not found in local state")
            token = str(row[0])
            mem = cur.execute(
                "SELECT value FROM ItemTable WHERE key = ?",
                ("cursorAuth/stripeMembershipType",),
            ).fetchone()
            membership = str(mem[0]) if mem and mem[0] else None
            return token, membership
        finally:
            con.close()

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
                raise ProviderError(
                    "auth_unavailable",
                    f"Cursor usage unauthorized (HTTP {status})",
                ) from exc
            raise ProviderError("upstream_error", f"Cursor usage failed (HTTP {status})") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("upstream_error", f"Cursor network error: {exc.reason}") from exc

        if status != 200:
            raise ProviderError("upstream_error", f"Cursor usage failed (HTTP {status})")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
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
        except ProviderError:
            pass
        if membership:
            return membership[:1].upper() + membership[1:]
        return "Cursor"

    @staticmethod
    def _clamp_pct(value: float) -> int:
        return max(0, min(100, int(round(value))))

    @staticmethod
    def _remaining_from_used_percent(used: Any) -> int | None:
        if used is None:
            return None
        try:
            return CursorProvider._clamp_pct(100.0 - float(used))
        except (TypeError, ValueError):
            return None

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

        primary = cursor_models if cursor_models is not None else other_models
        out: dict[str, Any] = {
            "provider": self.id,
            "displayName": self.display_name,
            "plan": plan_label,
            "remainingPercent": primary,
            "resetAt": reset_at,
            "status": "ok",
            "breakdown": breakdown,
        }
        if cursor_models is not None and other_models is not None:
            out["secondaryRemainingPercent"] = other_models
        return out
