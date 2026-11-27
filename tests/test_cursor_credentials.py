"""Deterministic Phase 11 tests for Cursor dual-source read-only credentials (ADR-0013)."""

from __future__ import annotations

import hashlib
import http.server
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "collector"
if str(COLLECTOR) not in sys.path:
    sys.path.insert(0, str(COLLECTOR))

from providers import ProviderError  # noqa: E402
from providers.cursor import (  # noqa: E402
    PLAN_PATH,
    USAGE_PATH,
    CursorProvider,
    _is_jwt_shaped,
)

# Obviously fake fixture values (never real JWTs or tokens).
IDE_JWT = "fakeide1.fakeide2.fakeide3"
IDE_OPAQUE = "opaque:ide:sessionvalue"
IDE_REFRESH = "fake-ide-refresh-only-value"
CLI_JWT = "fakecli1.fakecli2.fakecli3"
CLI_REFRESH = "fake-cli-refresh-only-value"

USAGE_OK = {
    "billingCycleEnd": "1756848242000",
    "planUsage": {
        "autoPercentUsed": 2,
        "apiPercentUsed": 40,
        "totalPercentUsed": 99,
        "remaining": 10,
        "limit": 100,
    },
}
PLAN_OK = {"planInfo": {"planName": "Pro"}}


def _make_state_db(
    path: Path,
    *,
    access_token: Any = None,
    refresh_token: str | None = IDE_REFRESH,
    membership: str | None = "pro",
) -> Path:
    con = sqlite3.connect(str(path))
    try:
        con.execute("CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)")
        if access_token is not None:
            con.execute(
                "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                ("cursorAuth/accessToken", access_token),
            )
        if refresh_token is not None:
            con.execute(
                "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                ("cursorAuth/refreshToken", refresh_token),
            )
        if membership is not None:
            con.execute(
                "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                ("cursorAuth/stripeMembershipType", membership),
            )
        con.commit()
    finally:
        con.close()
    return path


def _make_cli_auth(path: Path, payload: Any) -> Path:
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _fingerprint(path: Path) -> tuple[str, int]:
    st = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest, st.st_mtime_ns


def _assert_no_secrets_in_text(tc: unittest.TestCase, text: str) -> None:
    for secret in (IDE_JWT, IDE_OPAQUE, IDE_REFRESH, CLI_JWT, CLI_REFRESH):
        tc.assertNotIn(secret, text)
        tc.assertNotIn(secret[:8], text)


class _FakeCursorServer:
    """Local HTTP server recording (path, authorization, body) and scripting responses."""

    def __init__(self, handler_fn):
        self.handler_fn = handler_fn
        self.requests: list[tuple[str, str, str]] = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
                auth = self.headers.get("Authorization", "")
                outer.requests.append((self.path, auth, body))
                status, payload = outer.handler_fn(self.path, auth, body)
                raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                del format, args

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def __enter__(self) -> "_FakeCursorServer":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class ReaderTests(unittest.TestCase):
    """T1 — IDE and CLI candidate readers."""

    def test_jwt_shape_gate(self) -> None:
        self.assertTrue(_is_jwt_shaped(IDE_JWT))
        self.assertFalse(_is_jwt_shaped(IDE_OPAQUE))
        self.assertFalse(_is_jwt_shaped(""))
        self.assertFalse(_is_jwt_shaped("a.b"))
        self.assertFalse(_is_jwt_shaped("a.b.c.d"))
        self.assertFalse(_is_jwt_shaped("a..c"))
        self.assertFalse(_is_jwt_shaped(".b.c"))
        self.assertFalse(_is_jwt_shaped("a.b."))
        self.assertFalse(_is_jwt_shaped(None))
        self.assertFalse(_is_jwt_shaped(123))

    def test_ide_reader_outcomes_and_membership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 1. Valid JWT
            db_ok = _make_state_db(root / "ok.vscdb", access_token=IDE_JWT, membership="pro")
            tok, outcome, mem = CursorProvider(state_db=db_ok, cli_auth=root / "none.json")._read_ide_candidate()
            self.assertEqual((tok, outcome, mem), (IDE_JWT, None, "pro"))

            # 2. Non-JWT value -> unsupported format, value not returned
            db_opaque = _make_state_db(root / "opaque.vscdb", access_token=IDE_OPAQUE, membership="pro")
            tok, outcome, mem = CursorProvider(state_db=db_opaque, cli_auth=root / "none.json")._read_ide_candidate()
            self.assertIsNone(tok)
            self.assertEqual(outcome, "unsupported format")
            self.assertEqual(mem, "pro")

            # 3. Missing key -> no token, membership still read
            db_missing = _make_state_db(root / "missing.vscdb", access_token=None, membership="pro")
            tok, outcome, mem = CursorProvider(state_db=db_missing, cli_auth=root / "none.json")._read_ide_candidate()
            self.assertEqual((tok, outcome, mem), (None, "no token", "pro"))

            # 4. Non-SQLite file -> unreadable
            bad_db = root / "not-sqlite.vscdb"
            bad_db.write_text("definitely not sqlite", encoding="utf-8")
            tok, outcome, mem = CursorProvider(state_db=bad_db, cli_auth=root / "none.json")._read_ide_candidate()
            self.assertEqual((tok, outcome, mem), (None, "unreadable", None))

            # 5. Absent file -> not found
            tok, outcome, mem = CursorProvider(
                state_db=root / "absent.vscdb", cli_auth=root / "none.json"
            )._read_ide_candidate()
            self.assertEqual((tok, outcome, mem), (None, "not found", None))

    def test_cli_reader_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 6. Valid accessToken
            ok = _make_cli_auth(root / "ok.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            tok, outcome = CursorProvider(state_db=root / "none.vscdb", cli_auth=ok)._read_cli_candidate()
            self.assertEqual((tok, outcome), (CLI_JWT, None))

            # 7. Only refreshToken -> no token
            only_ref = _make_cli_auth(root / "ref.json", {"refreshToken": CLI_REFRESH})
            tok, outcome = CursorProvider(state_db=root / "none.vscdb", cli_auth=only_ref)._read_cli_candidate()
            self.assertEqual((tok, outcome), (None, "no token"))

            # 8. Invalid JSON and JSON array -> unreadable
            bad_json = _make_cli_auth(root / "bad.json", "{not json")
            tok, outcome = CursorProvider(state_db=root / "none.vscdb", cli_auth=bad_json)._read_cli_candidate()
            self.assertEqual((tok, outcome), (None, "unreadable"))

            arr_json = _make_cli_auth(root / "arr.json", ["not", "an", "object"])
            tok, outcome = CursorProvider(state_db=root / "none.vscdb", cli_auth=arr_json)._read_cli_candidate()
            self.assertEqual((tok, outcome), (None, "unreadable"))

            # 9. Absent CLI file -> not found
            tok, outcome = CursorProvider(
                state_db=root / "none.vscdb", cli_auth=root / "absent.json"
            )._read_cli_candidate()
            self.assertEqual((tok, outcome), (None, "not found"))


class OrderedFallbackAndSecurityTests(unittest.TestCase):
    """T2, T3, T4, T5, T6 — ordered fetch, fallback boundaries, read-only & secret checks."""

    def _assert_expected_meters(self, out: dict[str, Any]) -> None:
        self.assertEqual(out["status"], "ok")
        self.assertEqual([m["label"] for m in out["meters"]], ["Cursor Models", "Other Models"])
        self.assertEqual(out["meters"][0]["remainingPercent"], 98)
        self.assertEqual(out["meters"][1]["remainingPercent"], 60)
        self.assertEqual(out["secondaryRemainingPercent"], 60)

    def _assert_no_refresh_sent(self, requests: list[tuple[str, str, str]]) -> None:
        for _path, auth, body in requests:
            self.assertNotIn(IDE_REFRESH, auth)
            self.assertNotIn(IDE_REFRESH, body)
            self.assertNotIn(CLI_REFRESH, auth)
            self.assertNotIn(CLI_REFRESH, body)

    def test_1a_ide_jwt_accepted_sends_no_cli_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)

            def handler(path: str, auth: str, _body: str):
                if path == USAGE_PATH and auth == f"Bearer {IDE_JWT}":
                    return 200, USAGE_OK
                if path == PLAN_PATH and auth == f"Bearer {IDE_JWT}":
                    return 200, PLAN_OK
                return 500, {"error": "unexpected"}

            with _FakeCursorServer(handler) as srv:
                p = CursorProvider(state_db=db, cli_auth=cli)
                p.api_base = srv.url
                out = p.fetch_usage()
                self._assert_expected_meters(out)
                self.assertEqual(out["plan"], "Pro")
                self.assertEqual(
                    [(r[0], r[1]) for r in srv.requests],
                    [(USAGE_PATH, f"Bearer {IDE_JWT}"), (PLAN_PATH, f"Bearer {IDE_JWT}")],
                )
                self._assert_no_refresh_sent(srv.requests)
                _assert_no_secrets_in_text(self, json.dumps(out))
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

    def test_1b_ide_401_and_403_fall_back_to_cli_and_reuse_cli_for_plan(self) -> None:
        for reject_code in (401, 403):
            with self.subTest(reject_code=reject_code), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
                cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
                fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)

                def handler(path: str, auth: str, _body: str, code: int = reject_code):
                    if path == USAGE_PATH and auth == f"Bearer {IDE_JWT}":
                        return code, {"error": "unauthorized"}
                    if path == USAGE_PATH and auth == f"Bearer {CLI_JWT}":
                        return 200, USAGE_OK
                    if path == PLAN_PATH and auth == f"Bearer {CLI_JWT}":
                        return 200, PLAN_OK
                    return 500, {"error": "unexpected"}

                with _FakeCursorServer(handler) as srv:
                    p = CursorProvider(state_db=db, cli_auth=cli)
                    p.api_base = srv.url
                    out = p.fetch_usage()
                    self._assert_expected_meters(out)
                    self.assertEqual(
                        [(r[0], r[1]) for r in srv.requests],
                        [
                            (USAGE_PATH, f"Bearer {IDE_JWT}"),
                            (USAGE_PATH, f"Bearer {CLI_JWT}"),
                            (PLAN_PATH, f"Bearer {CLI_JWT}"),
                        ],
                    )
                    self._assert_no_refresh_sent(srv.requests)
                self.assertEqual(_fingerprint(db), fp_db)
                self.assertEqual(_fingerprint(cli), fp_cli)

    def test_1c_non_jwt_ide_never_sent_and_cli_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_OPAQUE)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)

            def handler(path: str, auth: str, _body: str):
                if path == USAGE_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, USAGE_OK
                if path == PLAN_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, PLAN_OK
                return 401, {"error": "unauthorized"}

            with _FakeCursorServer(handler) as srv:
                p = CursorProvider(state_db=db, cli_auth=cli)
                p.api_base = srv.url
                out = p.fetch_usage()
                self._assert_expected_meters(out)
                self.assertEqual(
                    [(r[0], r[1]) for r in srv.requests],
                    [(USAGE_PATH, f"Bearer {CLI_JWT}"), (PLAN_PATH, f"Bearer {CLI_JWT}")],
                )
                for _p, auth, body in srv.requests:
                    self.assertNotIn(IDE_OPAQUE, auth)
                    self.assertNotIn(IDE_OPAQUE, body)
                self._assert_no_refresh_sent(srv.requests)
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

    def test_1d_absent_ide_db_with_valid_cli_gives_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            fp_cli = _fingerprint(cli)

            def handler(path: str, auth: str, _body: str):
                if path == USAGE_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, USAGE_OK
                if path == PLAN_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, PLAN_OK
                return 401, {}

            with _FakeCursorServer(handler) as srv:
                p = CursorProvider(state_db=root / "missing.vscdb", cli_auth=cli)
                p.api_base = srv.url
                out = p.fetch_usage()
                self._assert_expected_meters(out)
                self.assertEqual(
                    [(r[0], r[1]) for r in srv.requests],
                    [(USAGE_PATH, f"Bearer {CLI_JWT}"), (PLAN_PATH, f"Bearer {CLI_JWT}")],
                )
                self._assert_no_refresh_sent(srv.requests)
            self.assertEqual(_fingerprint(cli), fp_cli)

    def test_1f_both_sources_fail_exact_outcome_messages(self) -> None:
        # Case 1: IDE 401 and CLI 401
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)
            with _FakeCursorServer(lambda _p, _a, _b: (401, {})) as srv:
                p = CursorProvider(state_db=db, cli_auth=cli)
                p.api_base = srv.url
                with self.assertRaises(ProviderError) as ctx:
                    p.fetch_usage()
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertEqual(
                ctx.exception.message,
                "Cursor usage unauthorized: IDE rejected (HTTP 401); CLI rejected (HTTP 401). "
                "Sign in to Cursor or the Cursor CLI (agent login).",
            )
            _assert_no_secrets_in_text(self, ctx.exception.message)
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

        # Case 2: IDE 403 and CLI absent
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
            fp_db = _fingerprint(db)
            with _FakeCursorServer(lambda _p, _a, _b: (403, {})) as srv:
                p = CursorProvider(state_db=db, cli_auth=root / "absent.json")
                p.api_base = srv.url
                with self.assertRaises(ProviderError) as ctx:
                    p.fetch_usage()
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertEqual(
                ctx.exception.message,
                "Cursor usage unauthorized: IDE rejected (HTTP 403); CLI not found. "
                "Sign in to Cursor or the Cursor CLI (agent login).",
            )
            _assert_no_secrets_in_text(self, ctx.exception.message)
            self.assertEqual(_fingerprint(db), fp_db)

        # Case 3: IDE unsupported format and CLI no token
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_OPAQUE)
            cli = _make_cli_auth(root / "auth.json", {"refreshToken": CLI_REFRESH})
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)
            with _FakeCursorServer(lambda _p, _a, _b: (200, USAGE_OK)) as srv:
                p = CursorProvider(state_db=db, cli_auth=cli)
                p.api_base = srv.url
                with self.assertRaises(ProviderError) as ctx:
                    p.fetch_usage()
                self.assertEqual(srv.requests, [])
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertEqual(
                ctx.exception.message,
                "Cursor usage unauthorized: IDE unsupported format; CLI no token. "
                "Sign in to Cursor or the Cursor CLI (agent login).",
            )
            _assert_no_secrets_in_text(self, ctx.exception.message)
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

        # Case 4: IDE unreadable and CLI unreadable
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "bad.vscdb"
            db.write_text("not sqlite", encoding="utf-8")
            cli = _make_cli_auth(root / "bad.json", "{broken")
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)
            p = CursorProvider(state_db=db, cli_auth=cli)
            with self.assertRaises(ProviderError) as ctx:
                p.fetch_usage()
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertEqual(
                ctx.exception.message,
                "Cursor usage unauthorized: IDE unreadable; CLI unreadable. "
                "Sign in to Cursor or the Cursor CLI (agent login).",
            )
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

    def test_t3_no_fallback_on_upstream_failures(self) -> None:
        # 1. Connection refused (URLError)
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        closed_port = sock.getsockname()[1]
        sock.close()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT})
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)
            p = CursorProvider(state_db=db, cli_auth=cli)
            p.api_base = f"http://127.0.0.1:{closed_port}"
            with self.assertRaises(ProviderError) as ctx:
                p.fetch_usage()
            self.assertEqual(ctx.exception.code, "upstream_error")
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

        # 2..5: HTTP 500, invalid JSON, JSON array, missing both percent fields
        cases = [
            ("http_500", 500, b'{"error":"boom"}'),
            ("invalid_json", 200, b"<html>not json</html>"),
            ("json_array", 200, b"[1, 2, 3]"),
            ("missing_percents", 200, json.dumps({"planUsage": {"remaining": 10}}).encode()),
        ]
        for name, status, payload in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
                cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT})
                fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)

                def handler(path: str, _auth: str, _body: str, st: int = status, body: bytes = payload):
                    if path == USAGE_PATH:
                        return st, body
                    return 200, PLAN_OK

                with _FakeCursorServer(handler) as srv:
                    p = CursorProvider(state_db=db, cli_auth=cli)
                    p.api_base = srv.url
                    with self.assertRaises(ProviderError) as ctx:
                        p.fetch_usage()
                    self.assertEqual(ctx.exception.code, "upstream_error")
                    for _path, auth, _b in srv.requests:
                        self.assertNotIn(CLI_JWT, auth)
                self.assertEqual(_fingerprint(db), fp_db)
                self.assertEqual(_fingerprint(cli), fp_cli)

    def test_t3_invalid_utf8_body_gives_upstream_error_without_cli_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT})
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)

            def handler(path: str, _auth: str, _body: str):
                if path == USAGE_PATH:
                    return 200, b"\xff\xfe\xfd"
                return 200, PLAN_OK

            with _FakeCursorServer(handler) as srv:
                p = CursorProvider(state_db=db, cli_auth=cli)
                p.api_base = srv.url
                with self.assertRaises(ProviderError) as ctx:
                    p.fetch_usage()
                self.assertEqual(ctx.exception.code, "upstream_error")
                self.assertEqual(ctx.exception.message, "Cursor usage response was not valid JSON")
                for _path, auth, _b in srv.requests:
                    self.assertNotIn(CLI_JWT, auth)
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)

    def test_t3_warm_cache_gives_stale_on_fake_500(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_JWT)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            cache_home = root / "cache"
            mode = {"status": 200}

            def handler(path: str, _auth: str, _body: str):
                if path == USAGE_PATH:
                    return (200, USAGE_OK) if mode["status"] == 200 else (500, {"error": "down"})
                return 200, PLAN_OK

            with _FakeCursorServer(handler) as srv:
                env = dict(os.environ)
                env["CURSOR_API_BASE"] = srv.url
                env["CURSOR_CLI_AUTH_FILE"] = str(cli)
                env["XDG_CACHE_HOME"] = str(cache_home)

                # Prime cache with 200
                r1 = subprocess.run(
                    [sys.executable, str(COLLECTOR / "ai-usage"), "status", "cursor", "--json", "--auth-file", str(db)],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(r1.returncode, 0)
                _assert_no_secrets_in_text(self, r1.stdout + r1.stderr)
                cache_file = cache_home / "horizon" / "usage-cursor.json"
                self.assertTrue(cache_file.is_file())
                _assert_no_secrets_in_text(self, cache_file.read_text(encoding="utf-8"))

                # Now 500 -> stale from cache, zero CLI requests
                mode["status"] = 500
                before_reqs = len(srv.requests)
                r2 = subprocess.run(
                    [sys.executable, str(COLLECTOR / "ai-usage"), "status", "cursor", "--json", "--auth-file", str(db)],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(r2.returncode, 1)
                payload = json.loads(r2.stdout)
                self.assertEqual(payload["status"], "stale")
                self.assertTrue(payload["stale"])
                _assert_no_secrets_in_text(self, r2.stdout + r2.stderr)
                for _path, auth, _b in srv.requests[before_reqs:]:
                    self.assertNotIn(CLI_JWT, auth)

    def test_t4_plan_info_401_falls_back_to_membership_without_retrying_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = _make_state_db(root / "state.vscdb", access_token=IDE_OPAQUE, membership="pro")
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})

            def handler(path: str, auth: str, _body: str):
                if path == USAGE_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, USAGE_OK
                if path == PLAN_PATH:
                    return 401, {"error": "plan unauthorized"}
                return 500, {}

            with _FakeCursorServer(handler) as srv:
                p = CursorProvider(state_db=db, cli_auth=cli)
                p.api_base = srv.url
                out = p.fetch_usage()
                self._assert_expected_meters(out)
                self.assertEqual(out["plan"], "Pro")
                self.assertEqual(
                    [(r[0], r[1]) for r in srv.requests],
                    [(USAGE_PATH, f"Bearer {CLI_JWT}"), (PLAN_PATH, f"Bearer {CLI_JWT}")],
                )

    def test_t5_detect_and_cli_subprocess_wiring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Neither present -> detect() raises auth_unavailable, no HTTP
            p_none = CursorProvider(state_db=root / "a.vscdb", cli_auth=root / "b.json")
            with self.assertRaises(ProviderError) as ctx:
                p_none.detect()
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertEqual(
                ctx.exception.message,
                "Cursor usage unauthorized: IDE not found; CLI not found. "
                "Sign in to Cursor or the Cursor CLI (agent login).",
            )

            # IDE-only and CLI-only each pass detect()
            db = _make_state_db(root / "state.vscdb", access_token=IDE_OPAQUE)
            cli = _make_cli_auth(root / "auth.json", {"accessToken": CLI_JWT, "refreshToken": CLI_REFRESH})
            CursorProvider(state_db=db, cli_auth=root / "absent.json").detect()
            CursorProvider(state_db=root / "absent.vscdb", cli_auth=cli).detect()

            # Subprocess end-to-end with --auth-file + CURSOR_CLI_AUTH_FILE + CURSOR_API_BASE
            fp_db, fp_cli = _fingerprint(db), _fingerprint(cli)

            def handler(path: str, auth: str, _body: str):
                if path == USAGE_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, USAGE_OK
                if path == PLAN_PATH and auth == f"Bearer {CLI_JWT}":
                    return 200, PLAN_OK
                return 401, {}

            with _FakeCursorServer(handler) as srv:
                env = dict(os.environ)
                env["CURSOR_API_BASE"] = srv.url
                env["CURSOR_CLI_AUTH_FILE"] = str(cli)
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(COLLECTOR / "ai-usage"),
                        "status",
                        "cursor",
                        "--json",
                        "--no-cache",
                        "--auth-file",
                        str(db),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                payload = json.loads(proc.stdout)
                self._assert_expected_meters(payload)
                _assert_no_secrets_in_text(self, proc.stdout + proc.stderr)
                self._assert_no_refresh_sent(srv.requests)
            self.assertEqual(_fingerprint(db), fp_db)
            self.assertEqual(_fingerprint(cli), fp_cli)


if __name__ == "__main__":
    unittest.main()
