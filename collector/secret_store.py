"""Minimal OS credential store for Horizon (KWallet / Secret Service via KDE).

Stores only opaque secrets identified by (provider, name). Horizon never
persists these values in config, cache, env files, logs, or the repository.
"""

from __future__ import annotations

import os
from typing import Any

APP_ID = "horizon"
FOLDER = "Horizon"


class SecretStoreError(RuntimeError):
    """OS credential store unavailable or operation failed."""


def _wallet_name() -> str:
    return os.environ.get("HORIZON_KWALLET_NAME") or "kdewallet"


def _iface() -> Any:
    try:
        import dbus  # type: ignore
    except ImportError as exc:
        raise SecretStoreError(
            "Python dbus module required for KWallet access (python3-dbus)"
        ) from exc
    try:
        bus = dbus.SessionBus()
        obj = bus.get_object("org.kde.kwalletd6", "/modules/kwalletd6")
        return dbus.Interface(obj, "org.kde.KWallet")
    except Exception as exc:  # noqa: BLE001
        raise SecretStoreError(f"Cannot connect to KWallet: {exc}") from exc


def _open(iface: Any) -> int:
    try:
        if not bool(iface.isEnabled()):
            raise SecretStoreError("KWallet is disabled")
        handle = int(iface.open(_wallet_name(), 0, APP_ID))
    except SecretStoreError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SecretStoreError(f"Cannot open KWallet: {exc}") from exc
    if handle < 0:
        raise SecretStoreError("KWallet open failed (denied or locked)")
    return handle


def _entry_key(provider: str, name: str) -> str:
    safe_p = "".join(c for c in provider if c.isalnum() or c in ("-", "_"))
    safe_n = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    if not safe_p or not safe_n:
        raise SecretStoreError("Invalid secret key")
    return f"{safe_p}/{safe_n}"


def get(provider: str, name: str) -> str | None:
    """Return secret value or None if missing."""
    iface = _iface()
    handle = _open(iface)
    key = _entry_key(provider, name)
    try:
        if not bool(iface.hasFolder(handle, FOLDER, APP_ID)):
            return None
        if not bool(iface.hasEntry(handle, FOLDER, key, APP_ID)):
            return None
        value = iface.readPassword(handle, FOLDER, key, APP_ID)
        text = str(value) if value is not None else ""
        return text if text else None
    finally:
        try:
            iface.close(handle, False, APP_ID)
        except Exception:  # noqa: BLE001
            pass


def set(provider: str, name: str, value: str) -> None:
    """Store secret in OS credential store (overwrites existing)."""
    if not value:
        raise SecretStoreError("Refusing to store empty secret")
    iface = _iface()
    handle = _open(iface)
    key = _entry_key(provider, name)
    try:
        if not bool(iface.hasFolder(handle, FOLDER, APP_ID)):
            if not bool(iface.createFolder(handle, FOLDER, APP_ID)):
                raise SecretStoreError("Cannot create Horizon KWallet folder")
        rc = int(iface.writePassword(handle, FOLDER, key, value, APP_ID))
        if rc != 0:
            raise SecretStoreError("KWallet writePassword failed")
    finally:
        try:
            iface.close(handle, False, APP_ID)
        except Exception:  # noqa: BLE001
            pass


def delete(provider: str, name: str) -> bool:
    """Delete secret if present. Returns True when an entry was removed."""
    iface = _iface()
    handle = _open(iface)
    key = _entry_key(provider, name)
    try:
        if not bool(iface.hasFolder(handle, FOLDER, APP_ID)):
            return False
        if not bool(iface.hasEntry(handle, FOLDER, key, APP_ID)):
            return False
        rc = int(iface.removeEntry(handle, FOLDER, key, APP_ID))
        return rc == 0
    finally:
        try:
            iface.close(handle, False, APP_ID)
        except Exception:  # noqa: BLE001
            pass


def configured(provider: str, name: str) -> bool:
    return get(provider, name) is not None
