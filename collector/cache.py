"""Last-successful normalized usage cache (XDG)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def cache_dir() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "horizon"


def cache_path(provider_id: str) -> Path:
    safe = "".join(c for c in provider_id if c.isalnum() or c in ("-", "_"))
    return cache_dir() / f"usage-{safe}.json"


def write_success(provider_id: str, data: dict[str, Any]) -> Path:
    """Persist normalized ok payload only."""
    if data.get("status") != "ok":
        raise ValueError("refusing to cache non-ok payload")
    # Strip any accidental secret-looking keys
    forbidden = ("access_token", "refresh_token", "id_token", "authorization", "cookie")
    for key in forbidden:
        if key in data:
            raise ValueError(f"refusing to cache forbidden field: {key}")

    path = cache_path(provider_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "fetchedAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "provider": provider_id,
        "data": {
            k: data[k]
            for k in (
                "provider",
                "displayName",
                "plan",
                "remainingPercent",
                "resetAt",
                "status",
                "secondaryRemainingPercent",
            )
            if k in data
        },
    }
    fd, tmp_name = tempfile.mkstemp(prefix=".usage-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(envelope, tmp, indent=2)
            tmp.write("\n")
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def read_success(provider_id: str) -> dict[str, Any] | None:
    path = cache_path(provider_id)
    if not path.is_file():
        return None
    try:
        envelope = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(envelope, dict):
        return None
    data = envelope.get("data")
    if not isinstance(data, dict) or data.get("status") != "ok":
        return None
    if envelope.get("provider") != provider_id and data.get("provider") != provider_id:
        return None
    fetched_at = envelope.get("fetchedAt")
    if not isinstance(fetched_at, str):
        return None
    return {"fetchedAt": fetched_at, "data": data}


def stale_payload(provider_id: str, display_name: str, live_error: str) -> dict[str, Any] | None:
    cached = read_success(provider_id)
    if not cached:
        return None
    data = dict(cached["data"])
    data["status"] = "stale"
    data["stale"] = True
    data["fetchedAt"] = cached["fetchedAt"]
    data["error"] = live_error
    data.setdefault("displayName", display_name)
    data.setdefault("provider", provider_id)
    return data
