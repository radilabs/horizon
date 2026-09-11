#!/usr/bin/env python3
"""StepFun auth helper for Plasma settings (no token in process argv).

Commands (stdout is a single status token; never prints secrets):
  status    -> missing | working | auth_failed | store_error
  clipboard -> read Oasis token from clipboard, store in KWallet, verify
  stdin     -> read Oasis token from stdin, store in KWallet, verify
  clear     -> delete stored token
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from secret_store import SecretStoreError  # noqa: E402
from secret_store import delete as secret_delete  # noqa: E402
from secret_store import get as secret_get  # noqa: E402
from secret_store import set as secret_set  # noqa: E402


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def looks_like_oasis_token(token: str) -> bool:
    # Oasis tokens are JWTs or access...refresh pairs; reject obvious junk.
    return len(token) >= 80 and "." in token


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


def verify_token(token: str) -> str:
    """Return working | auth_failed without leaking token material.

    Uses fetch_usage so a stored but expired Oasis pair can take the same
    single bounded refresh path as the collector (KWallet updated only after
    a successful usage probe).
    """
    from providers.stepfun import StepFunProvider  # noqa: WPS433
    from providers import ProviderError  # noqa: WPS433

    # Token argument is the value just stored or read; fetch_usage reloads
    # from KWallet so callers must persist first.
    del token
    try:
        StepFunProvider().fetch_usage()
        return "working"
    except ProviderError as exc:
        if exc.code == "auth_unavailable":
            return "auth_failed"
        return "auth_failed"
    except Exception:  # noqa: BLE001
        return "auth_failed"


def store_and_verify(token: str) -> tuple[str, int]:
    token = (token or "").strip()
    if not token:
        print("empty")
        return "empty", 1
    if not looks_like_oasis_token(token):
        print("invalid")
        return "invalid", 1
    try:
        secret_set("stepfun", "oasis-token", token)
    except SecretStoreError as exc:
        eprint(str(exc))
        print("store_error")
        return "store_error", 1
    result = verify_token(token)
    print(result)
    return result, (0 if result == "working" else 1)


def cmd_status() -> int:
    try:
        token = secret_get("stepfun", "oasis-token")
    except SecretStoreError as exc:
        eprint(str(exc))
        print("store_error")
        return 1
    if not token:
        print("missing")
        return 0
    print(verify_token(token))
    return 0


def cmd_clipboard() -> int:
    result, code = store_and_verify(read_clipboard())
    if result in {"working", "auth_failed"}:
        clear_clipboard()
    return code


def cmd_stdin() -> int:
    _result, code = store_and_verify(sys.stdin.read())
    return code


def cmd_clear() -> int:
    try:
        secret_delete("stepfun", "oasis-token")
    except SecretStoreError as exc:
        eprint(str(exc))
        print("store_error")
        return 1
    print("missing")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"status", "clipboard", "stdin", "clear"}:
        eprint("usage: stepfun_auth_helper.py {status|clipboard|stdin|clear}")
        return 2
    cmd = argv[1]
    if cmd == "status":
        return cmd_status()
    if cmd == "clipboard":
        return cmd_clipboard()
    if cmd == "stdin":
        return cmd_stdin()
    return cmd_clear()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
