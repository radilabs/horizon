"""Provider-neutral usage meters (Phase 7).

`meters` is the canonical ordered quota list. Compatibility fields are
projections of that list so existing CLI, cache, and QML consumers keep
working. Percent values are remaining quota, 0–100, never percent used.
"""

from __future__ import annotations

from typing import Any


def project_ok(
    *,
    provider: str,
    display_name: str,
    plan: str | None,
    meters: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a successful normalized payload from an ordered meter list."""
    copied = [_copy_meter(meter) for meter in meters]
    if not copied:
        raise ValueError("ok usage requires at least one meter")
    first = copied[0]
    out: dict[str, Any] = {
        "provider": provider,
        "displayName": display_name,
        "plan": plan,
        "remainingPercent": first["remainingPercent"],
        "resetAt": first.get("resetAt"),
        "status": "ok",
        "meters": copied,
        "breakdown": [dict(meter) for meter in copied],
    }
    if len(copied) > 1:
        out["secondaryRemainingPercent"] = copied[1]["remainingPercent"]
    return out


def meters_from_payload(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Read meters from a Phase 7 payload or a pre-Phase-7 cache.

    Preference order: `meters`, then `breakdown`, then the unlabeled
    primary/secondary compatibility fields. Missing quota returns [].
    """
    meters = data.get("meters")
    if isinstance(meters, list) and meters:
        return [_copy_meter(meter) for meter in meters if isinstance(meter, dict)]
    breakdown = data.get("breakdown")
    if isinstance(breakdown, list) and breakdown:
        return [_copy_meter(meter) for meter in breakdown if isinstance(meter, dict)]

    remaining = data.get("remainingPercent")
    if not _is_percent(remaining):
        return []
    # Pre-Phase-7 Codex stored one reset on the payload and an unlabeled
    # secondary percent with no reset of its own. Duplicate labels are allowed;
    # order distinguishes the meters.
    rows = [_legacy_meter("Usage limit", int(remaining), data.get("resetAt"))]
    secondary = data.get("secondaryRemainingPercent")
    if _is_percent(secondary):
        rows.append(_legacy_meter("Usage limit", int(secondary), None))
    return rows


def _copy_meter(meter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(meter, dict):
        raise ValueError("meter must be an object")
    label = meter.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("meter label must be a non-empty string")
    remaining = meter.get("remainingPercent")
    if not _is_percent(remaining):
        raise ValueError("meter remainingPercent must be an integer 0–100")
    copied: dict[str, Any] = {
        "label": label,
        "remainingPercent": int(remaining),
    }
    reset_at = meter.get("resetAt")
    if isinstance(reset_at, str) and reset_at:
        copied["resetAt"] = reset_at
    return copied


def _legacy_meter(label: str, remaining: int, reset_at: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"label": label, "remainingPercent": remaining}
    if isinstance(reset_at, str) and reset_at:
        row["resetAt"] = reset_at
    return row


def _is_percent(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100
