"""StepFun Step Plan provider — Oasis token from OS secret store + Dashboard APIs."""

from __future__ import annotations

import base64
import json
import os
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from secret_store import SecretStoreError
from secret_store import get as secret_get
from secret_store import set as secret_set

from . import ProviderError

PROVIDER_ID = "stepfun"
SECRET_NAME = "oasis-token"
DEFAULT_API_BASE = "https://platform.stepfun.ai"
# CodexBar historically used platform.stepfun.com + app id 10300; current web
# sessions observed on platform.stepfun.ai use app_id from the refresh JWT
# (commonly 20700). Prefer deriving app id from the token.
RATE_LIMIT_PATH = "/api/step.openapi.devcenter.Dashboard/QueryStepPlanRateLimit"
PLAN_STATUS_PATH = "/api/step.openapi.devcenter.Dashboard/GetStepPlanStatus"
REFRESH_PATH = "/passport/proto.api.passport.v1.PassportService/RefreshToken"
FALLBACK_OASIS_APP_ID = "20700"
_REFRESH_LOCK = threading.Lock()


class StepFunProvider:
    id = PROVIDER_ID
    display_name = "StepFun"

    def __init__(self) -> None:
        self.api_base = os.environ.get("STEPFUN_API_BASE", DEFAULT_API_BASE).rstrip("/")

    def detect(self) -> None:
        token = self._load_token()
        if not token:
            raise ProviderError(
                "auth_unavailable",
                "StepFun Oasis token not configured (run: ai-usage auth stepfun set)",
            )

    def fetch_usage(self, *, force_refresh: bool = False) -> dict[str, Any]:
        del force_refresh
        token = self._load_token()
        if not token:
            raise ProviderError(
                "auth_unavailable",
                "StepFun Oasis token not configured (run: ai-usage auth stepfun set)",
            )
        webid = derive_oasis_webid(token)
        if not webid:
            raise ProviderError(
                "auth_unavailable",
                "StepFun Oasis token missing device_id (cannot derive Oasis-Webid)",
            )
        app_id = derive_oasis_app_id(token) or FALLBACK_OASIS_APP_ID
        try:
            usage = self._post_json(RATE_LIMIT_PATH, token, webid, app_id, {})
        except ProviderError as exc:
            if exc.code != "auth_unavailable":
                raise
            token = self._recover_after_auth_rejection(token)
            webid = derive_oasis_webid(token) or webid
            app_id = derive_oasis_app_id(token) or app_id
            usage = self._post_json(RATE_LIMIT_PATH, token, webid, app_id, {})
        plan_label = self._plan_label(token, webid, app_id)
        return self._normalize(usage, plan_label)

    def _recover_after_auth_rejection(self, previous_token: str) -> str:
        """One bounded Oasis refresh using stored material only. Replaces KWallet only after validation."""
        with _REFRESH_LOCK:
            current = self._load_token() or previous_token
            webid = derive_oasis_webid(current)
            if not webid:
                raise ProviderError(
                    "auth_unavailable",
                    "StepFun Oasis token rejected; replace it in widget settings or: ai-usage auth stepfun set",
                )
            app_id = derive_oasis_app_id(current) or FALLBACK_OASIS_APP_ID
            if current != previous_token:
                try:
                    self._post_json(RATE_LIMIT_PATH, current, webid, app_id, {})
                    return current
                except ProviderError as exc:
                    if exc.code != "auth_unavailable":
                        raise
            try:
                refreshed = self._refresh_oasis_token(current, webid, app_id)
            except ProviderError:
                raise ProviderError(
                    "auth_unavailable",
                    "StepFun Oasis token rejected; replace it in widget settings or: ai-usage auth stepfun set",
                ) from None
            refreshed_webid = derive_oasis_webid(refreshed) or webid
            refreshed_app = derive_oasis_app_id(refreshed) or app_id
            try:
                self._post_json(RATE_LIMIT_PATH, refreshed, refreshed_webid, refreshed_app, {})
            except ProviderError:
                # Keep the previous KWallet value.
                raise ProviderError(
                    "auth_unavailable",
                    "StepFun Oasis token rejected; replace it in widget settings or: ai-usage auth stepfun set",
                ) from None
            try:
                secret_set(PROVIDER_ID, SECRET_NAME, refreshed)
            except SecretStoreError:
                # Validated token still used for this request; store write failure is not a silent wipe.
                pass
            return refreshed

    def _refresh_oasis_token(self, token: str, webid: str, app_id: str) -> str:
        data = self._post_json(
            REFRESH_PATH,
            token,
            webid,
            app_id,
            {},
            oasis_token_header=True,
        )
        combined = combine_oasis_token_from_refresh(data)
        if not combined:
            raise ProviderError("auth_unavailable", "StepFun refresh response had no usable token")
        return combined

    def _load_token(self) -> str | None:
        try:
            value = secret_get(PROVIDER_ID, SECRET_NAME)
        except SecretStoreError as exc:
            raise ProviderError("auth_unavailable", f"Credential store unavailable: {exc}") from exc
        if value is None:
            return None
        text = value.strip()
        return text or None

    def _plan_label(self, token: str, webid: str, app_id: str) -> str:
        try:
            status = self._post_json(PLAN_STATUS_PATH, token, webid, app_id, {})
        except ProviderError:
            return "Step Plan"
        sub = status.get("subscription") if isinstance(status, dict) else None
        if isinstance(sub, dict):
            name = sub.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return "Step Plan"

    def _post_json(
        self,
        path: str,
        token: str,
        webid: str,
        app_id: str,
        body: dict[str, Any],
        *,
        oasis_token_header: bool = False,
    ) -> dict[str, Any]:
        url = self.api_base + path
        raw_body = json.dumps(body).encode()
        req = urllib.request.Request(url, data=raw_body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("oasis-appid", str(app_id))
        req.add_header("oasis-platform", "web")
        req.add_header("oasis-webid", webid)
        if oasis_token_header:
            req.add_header("Oasis-Token", token)
        req.add_header("Cookie", f"Oasis-Token={token}; Oasis-Webid={webid}")
        req.add_header("Origin", self.api_base)
        req.add_header("Referer", self.api_base + "/")
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
            body_txt = ""
            try:
                body_txt = exc.read().decode("utf-8", errors="replace")[:200]
            except Exception:  # noqa: BLE001
                pass
            lower = body_txt.lower()
            if status in (401, 403) or "auth" in lower or "embezzl" in lower or "token" in lower:
                raise ProviderError(
                    "auth_unavailable",
                    f"StepFun usage unauthorized (HTTP {status})",
                ) from exc
            raise ProviderError("upstream_error", f"StepFun request failed (HTTP {status})") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("upstream_error", f"StepFun network error: {exc.reason}") from exc

        if status != 200:
            raise ProviderError("upstream_error", f"StepFun request failed (HTTP {status})")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderError("upstream_error", "StepFun response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderError("upstream_error", "StepFun response had unexpected shape")
        # API often wraps success as status==1
        api_status = data.get("status")
        if api_status is not None and api_status != 1:
            msg = data.get("message") or data.get("desc") or "StepFun API status not ok"
            text = str(msg).lower()
            if "auth" in text or "token" in text or "embezzl" in text:
                raise ProviderError("auth_unavailable", "StepFun authentication rejected")
            raise ProviderError("upstream_error", "StepFun API returned an error status")
        return data

    def _normalize(self, usage: dict[str, Any], plan_label: str) -> dict[str, Any]:
        credit = is_credit_plan(usage)
        if credit:
            breakdown = credit_breakdown(usage)
        else:
            breakdown = window_breakdown(usage)

        if not breakdown:
            raise ProviderError("upstream_error", "StepFun usage contained no usable meters")

        primary = breakdown[0]
        out: dict[str, Any] = {
            "provider": self.id,
            "displayName": self.display_name,
            "plan": plan_label,
            "remainingPercent": primary["remainingPercent"],
            "resetAt": primary.get("resetAt"),
            "status": "ok",
            "breakdown": breakdown,
        }
        if len(breakdown) > 1:
            out["secondaryRemainingPercent"] = breakdown[1]["remainingPercent"]
        return out


def combine_oasis_token_from_refresh(payload: dict[str, Any]) -> str | None:
    """Build stored Oasis token from a RefreshToken JSON body. Never logs values."""
    access = _token_raw(payload.get("accessToken") or payload.get("access_token"))
    refresh = _token_raw(payload.get("refreshToken") or payload.get("refresh_token"))
    if access and refresh:
        return f"{access}...{refresh}"
    return access or refresh


def _token_raw(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        raw = value.get("raw")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def derive_oasis_webid(token: str) -> str | None:
    """Derive Oasis-Webid from JWT device_id (refresh half preferred)."""
    halves = token.split("...")
    for half in reversed(halves):
        device_id = _jwt_claim(half.strip(), "device_id")
        if isinstance(device_id, str) and device_id:
            return device_id
    return None


def derive_oasis_app_id(token: str) -> str | None:
    """Derive oasis-appid from refresh JWT app_id when present."""
    halves = token.split("...")
    for half in reversed(halves):
        app_id = _jwt_claim(half.strip(), "app_id")
        if app_id is None:
            continue
        if isinstance(app_id, bool):
            continue
        if isinstance(app_id, (int, float)):
            return str(int(app_id))
        if isinstance(app_id, str) and app_id.strip().isdigit():
            return app_id.strip()
    return None


def _jwt_claim(jwt: str, claim: str) -> Any:
    parts = jwt.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    pad = "=" * (-len(payload) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload + pad)
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data.get(claim)


def _jwt_device_id(jwt: str) -> str | None:
    device_id = _jwt_claim(jwt, "device_id")
    return device_id if isinstance(device_id, str) and device_id else None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_epoch(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = int(value)
        return n if n > 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text or text == "0":
            return None
        try:
            n = int(float(text))
        except ValueError:
            return None
        return n if n > 0 else None
    return None


def _iso_from_epoch(epoch: int | None) -> str | None:
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _clamp_pct_from_left_rate(left_rate: float) -> int:
    return max(0, min(100, int(round(left_rate * 100.0))))


def is_credit_plan(usage: dict[str, Any]) -> bool:
    """Classify by payload shape (CodexBar-compatible), not plan_family alone."""
    five_reset = _as_epoch(usage.get("five_hour_usage_reset_time"))
    week_reset = _as_epoch(usage.get("weekly_usage_reset_time"))
    has_live_window = five_reset is not None or week_reset is not None
    if has_live_window:
        return False

    credit = usage.get("plan_credit_rate_limit")
    has_credit = False
    if isinstance(credit, dict):
        if credit.get("subscription_credit_left_rate") is not None:
            has_credit = True
        if credit.get("topup_credit_left_rate") is not None:
            has_credit = True
        buckets = credit.get("credit_buckets")
        if isinstance(buckets, list) and buckets:
            has_credit = True
    if has_credit:
        return True

    family = _as_float(usage.get("plan_family"))
    return family == 2.0


def window_breakdown(usage: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    five = _as_float(usage.get("five_hour_usage_left_rate"))
    week = _as_float(usage.get("weekly_usage_left_rate"))
    if five is not None:
        line: dict[str, Any] = {
            "label": "5-Hour Usage",
            "remainingPercent": _clamp_pct_from_left_rate(five),
        }
        reset = _iso_from_epoch(_as_epoch(usage.get("five_hour_usage_reset_time")))
        if reset:
            line["resetAt"] = reset
        lines.append(line)
    if week is not None:
        line = {
            "label": "Weekly Usage",
            "remainingPercent": _clamp_pct_from_left_rate(week),
        }
        reset = _iso_from_epoch(_as_epoch(usage.get("weekly_usage_reset_time")))
        if reset:
            line["resetAt"] = reset
        lines.append(line)
    return lines


def credit_breakdown(usage: dict[str, Any]) -> list[dict[str, Any]]:
    credit = usage.get("plan_credit_rate_limit")
    if not isinstance(credit, dict):
        return []

    lines: list[dict[str, Any]] = []
    combined = _combined_credit_left_rate(credit)
    if combined is not None:
        line: dict[str, Any] = {
            "label": "Credits",
            "remainingPercent": _clamp_pct_from_left_rate(combined),
        }
        reset = _iso_from_epoch(_as_epoch(credit.get("subscription_credit_reset_time")))
        if reset:
            line["resetAt"] = reset
        lines.append(line)
        return lines

    # Fallback: show independent meaningful meters (do not add rates).
    sub = _as_float(credit.get("subscription_credit_left_rate"))
    if sub is not None:
        line = {
            "label": "Subscription Credits",
            "remainingPercent": _clamp_pct_from_left_rate(sub),
        }
        reset = _iso_from_epoch(_as_epoch(credit.get("subscription_credit_reset_time")))
        if reset:
            line["resetAt"] = reset
        lines.append(line)

    top = _as_float(credit.get("topup_credit_left_rate"))
    if top is not None and sub is None:
        lines.append(
            {
                "label": "Top-up Credits",
                "remainingPercent": _clamp_pct_from_left_rate(top),
            }
        )
    return lines


def _combined_credit_left_rate(credit: dict[str, Any]) -> float | None:
    buckets = credit.get("credit_buckets")
    if isinstance(buckets, list) and buckets:
        totals: list[float] = []
        residuals: list[float] = []
        for bucket in buckets:
            if not isinstance(bucket, dict):
                return None
            total = _as_float(bucket.get("credit_total"))
            residual = _as_float(bucket.get("credit_residual"))
            if total is None or residual is None or total <= 0 or residual < 0 or residual > total:
                return None
            totals.append(total)
            residuals.append(residual)
        if len(totals) == len(buckets) and totals:
            return sum(residuals) / sum(totals)

    sub = _as_float(credit.get("subscription_credit_left_rate"))
    if sub is not None:
        return sub
    return _as_float(credit.get("topup_credit_left_rate"))
