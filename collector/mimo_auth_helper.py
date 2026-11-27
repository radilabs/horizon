#!/usr/bin/env python3
"""Xiaomi MiMo Token Plan auth helper for Plasma settings (no key in process argv).

Usage: mimo_auth_helper.py {status|clipboard|stdin|clear} [region]

Commands (stdout is a single status token; never prints secrets):
  status    -> missing | working | auth_failed | unavailable | store_error
  clipboard -> read tp- key from clipboard, validate, store in KWallet, verify
  stdin     -> read tp- key from stdin, validate, store in KWallet, verify
  clear     -> delete stored key (prints cleared)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from providers import ProviderError  # noqa: E402
from providers.mimo import (  # noqa: E402
    DEFAULT_REGION,
    PROVIDER_ID,
    REGIONS,
    SECRET_NAME,
    MiMoProvider,
    is_valid_token_plan_key,
)
from secret_store import SecretStoreError  # noqa: E402
from secret_store import delete as secret_delete  # noqa: E402
from secret_store import get as secret_get  # noqa: E402
from secret_store import set as secret_set  # noqa: E402


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def read_clipboard() -> str:
    # Prefer Wayland clipboard; fall back to Klipper.
    try:
        proc = subprocess.run(
            ["wl-paste", "-n"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout and proc.stdout.strip():
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        proc = subprocess.run(
            [
                "qdbus6",
                "org.kde.klipper",
                "/klipper",
                "org.kde.klipper.klipper.getClipboardContents",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout and proc.stdout.strip():
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def clear_clipboard() -> None:
    try:
        subprocess.run(["wl-copy", "--clear"], check=False, capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        subprocess.run(
            [
                "qdbus6",
                "org.kde.klipper",
                "/klipper",
                "org.kde.klipper.klipper.clearClipboardContents",
            ],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def verify_key(region: str) -> str:
    """Return working | auth_failed | unavailable without leaking key material."""
    try:
        MiMoProvider(region=region).fetch_usage()
        return "working"
    except ProviderError as exc:
        if exc.code == "auth_unavailable":
            return "auth_failed"
        return "unavailable"
    except Exception:  # noqa: BLE001
        return "unavailable"


def store_and_verify(key: str, region: str) -> tuple[str, int]:
    key = (key or "").strip()
    if not key:
        print("empty")
        return "empty", 1
    if not is_valid_token_plan_key(key):
        print("invalid")
        return "invalid", 1
    try:
        secret_set(PROVIDER_ID, SECRET_NAME, key)
    except SecretStoreError as exc:
        eprint(str(exc))
        print("store_error")
        return "store_error", 1
    result = verify_key(region)
    print(result)
    return result, (0 if result == "working" else 1)


def cmd_status(region: str) -> int:
    try:
        key = secret_get(PROVIDER_ID, SECRET_NAME)
    except SecretStoreError as exc:
        eprint(str(exc))
        print("store_error")
        return 1
    if not key:
        print("missing")
        return 0
    print(verify_key(region))
    return 0


def cmd_clipboard(region: str) -> int:
    result, code = store_and_verify(read_clipboard(), region)
    if result in {"working", "auth_failed", "unavailable"}:
        clear_clipboard()
    return code


def cmd_stdin(region: str) -> int:
    _result, code = store_and_verify(sys.stdin.read(), region)
    return code


def cmd_clear() -> int:
    try:
        secret_delete(PROVIDER_ID, SECRET_NAME)
    except SecretStoreError as exc:
        eprint(str(exc))
        print("store_error")
        return 1
    print("cleared")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3) or argv[1] not in {"status", "clipboard", "stdin", "clear"}:
        eprint("usage: mimo_auth_helper.py {status|clipboard|stdin|clear} [sgp|cn|ams]")
        return 2
    cmd = argv[1]
    region = argv[2] if len(argv) == 3 else DEFAULT_REGION
    if region not in REGIONS:
        eprint(f"invalid region: {region}")
        return 2
    if cmd == "status":
        return cmd_status(region)
    if cmd == "clipboard":
        return cmd_clipboard(region)
    if cmd == "stdin":
        return cmd_stdin(region)
    return cmd_clear()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
