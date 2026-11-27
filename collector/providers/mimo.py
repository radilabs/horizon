"""Xiaomi MiMo Token Plan provider — KWallet key + official GET /v1/platform/token_plan."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from secret_store import SecretStoreError
from secret_store import get as secret_get

from . import ProviderError
from .contract import project_ok

PROVIDER_ID = "mimo"
SECRET_NAME = "token-plan-key"
REGIONS = ("sgp", "cn", "ams")
DEFAULT_REGION = "sgp"
TOKEN_PLAN_PATH = "/v1/platform/token_plan"

_TIER_LABELS = {
    "lite": "Lite",
    "standard": "Standard",
    "pro": "Pro",
    "max": "Max",
}
_PERIOD_LABELS = {
    "year": "Annual",
    "month": "Monthly",
}


def is_valid_token_plan_key(value: Any) -> bool:
    """Shape check only: non-empty str, starts with tp-, no whitespace, 8..256 chars."""
    if not isinstance(value, str):
        return False
    if not value.startswith("tp-"):
        return False
    if not (8 <= len(value) <= 256):
        return False
    return not any(ch.isspace() for ch in value)


def endpoint_url(region: str, api_base: str | None = None) -> str:
    """Build the single official Token Plan URL for the configured region (or test override)."""
    if api_base:
        return api_base.rstrip("/") + TOKEN_PLAN_PATH
    return f"https://token-plan-{region}.xiaomimimo.com{TOKEN_PLAN_PATH}"


def normalize_plan(plan_code: Any) -> str | None:
    """Map documented tier/period codes to readable names; preserve unknown codes sanitized."""
    if not isinstance(plan_code, str):
        return None
    cleaned = "".join(ch for ch in plan_code.strip() if ch.isprintable())[:64]
    if not cleaned:
        return None
    if ":" in cleaned:
        tier_raw, suffix_raw = cleaned.split(":", 1)
        tier = _TIER_LABELS.get(tier_raw.lower())
        suffix = _PERIOD_LABELS.get(suffix_raw.lower())
        if tier and suffix:
            return f"{tier} · {suffix}"
        return cleaned
    tier = _TIER_LABELS.get(cleaned.lower())
    return tier if tier else cleaned


def _parse_period_end(period: Any) -> str | None:
    if not isinstance(period, dict):
        return None
    end_at = period.get("end_at")
    if not isinstance(end_at, str):
        return None
    try:
        dt = datetime.strptime(end_at.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return dt.isoformat()


class MiMoProvider:
    id = PROVIDER_ID
    display_name = "Xiaomi MiMo"
    REGIONS = REGIONS

    def __init__(self, region: str = DEFAULT_REGION) -> None:
        if region not in REGIONS:
            raise ProviderError(
                "provider_unavailable",
                f"Unsupported Xiaomi MiMo region: {region!r} (expected one of: {', '.join(REGIONS)})",
            )
        self.region = region
        env_base = os.environ.get("MIMO_API_BASE")
        self.api_base: str | None = env_base.rstrip("/") if env_base else None

    def _load_key(self) -> str:
        try:
            value = secret_get(PROVIDER_ID, SECRET_NAME)
        except SecretStoreError as exc:
            raise ProviderError("auth_unavailable", f"Credential store unavailable: {exc}") from exc
        if value is None or (isinstance(value, str) and not value):
            raise ProviderError(
                "auth_unavailable",
                "Xiaomi MiMo Token Plan key not configured (run: ai-usage auth mimo set)",
            )
        if not is_valid_token_plan_key(value):
            raise ProviderError(
                "auth_unavailable",
                "Xiaomi MiMo Token Plan key has invalid format (expected a tp- key with no whitespace)",
            )
        return value

    def detect(self) -> None:
        self._load_key()

    def fetch_usage(self, *, force_refresh: bool = False) -> dict[str, Any]:
        del force_refresh
        key = self._load_key()
        data = self._get_json(key)
        return self._normalize(data)

    def _get_json(self, key: str) -> dict[str, Any]:
        url = endpoint_url(self.region, self.api_base)
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {key}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise ProviderError(
                    "auth_unavailable",
                    f"Xiaomi MiMo rejected the Token Plan key for region {self.region} (HTTP 401). "
                    "Check the key and the configured region.",
                ) from exc
            raise ProviderError(
                "upstream_error",
                f"Xiaomi MiMo usage failed (HTTP {exc.code})",
            ) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            reason = getattr(exc, "reason", exc)
            raise ProviderError("upstream_error", f"Xiaomi MiMo network error: {reason}") from exc

        if status != 200:
            raise ProviderError("upstream_error", f"Xiaomi MiMo usage failed (HTTP {status})")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ProviderError("upstream_error", "Xiaomi MiMo response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderError("upstream_error", "Xiaomi MiMo response had unexpected shape")
        return data

    def _normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        quota = payload.get("quota")
        if not isinstance(quota, dict):
            raise ProviderError("upstream_error", "Xiaomi MiMo usage missing quota object")

        total = quota.get("total_credits")
        if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
            raise ProviderError("upstream_error", "Xiaomi MiMo usage has invalid total_credits")

        rem = quota.get("remaining_credits")
        if rem is None:
            used = quota.get("used_credits")
            if isinstance(used, bool) or not isinstance(used, int):
                raise ProviderError(
                    "upstream_error",
                    "Xiaomi MiMo usage missing remaining_credits and used_credits",
                )
            rem_val = max(0, total - used)
        else:
            if isinstance(rem, bool) or not isinstance(rem, int):
                raise ProviderError("upstream_error", "Xiaomi MiMo usage has invalid remaining_credits")
            rem_val = rem

        clamped_rem = max(0, min(total, rem_val))
        remaining_pct = max(0, min(100, int(round(clamped_rem / total * 100))))

        meter: dict[str, Any] = {
            "label": "Credits",
            "remainingPercent": remaining_pct,
        }
        reset_at = _parse_period_end(payload.get("period"))
        if reset_at:
            meter["resetAt"] = reset_at

        return project_ok(
            provider=self.id,
            display_name=self.display_name,
            plan=normalize_plan(payload.get("plan_code")),
            meters=[meter],
        )
