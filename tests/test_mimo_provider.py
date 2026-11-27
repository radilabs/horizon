"""Deterministic Phase 12 tests for Xiaomi MiMo Token Plan provider (offline, fake fixtures)."""

from __future__ import annotations

import builtins
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "collector"
if str(COLLECTOR) not in sys.path:
    sys.path.insert(0, str(COLLECTOR))

from providers import ProviderError  # noqa: E402
from providers.mimo import (  # noqa: E402
    TOKEN_PLAN_PATH,
    MiMoProvider,
    endpoint_url,
    is_valid_token_plan_key,
    normalize_plan,
)
from secret_store import SecretStoreError  # noqa: E402

FIXTURE_KEY = "tp-fake-fixture-key-0001"

MONTHLY_BODY = {
    "plan_code": "pro:month",
    "auto_renew": True,
    "claw_enabled": False,
    "period": {
        "start_at": "2026-11-11 21:05:27",
        "end_at": "2026-12-11 23:59:59",
    },
    "quota": {
        "total_credits": 4_100_000_000,
        "used_credits": 1_400_000_000,
        "remaining_credits": 2_700_000_000,
    },
}

ANNUAL_BODY = {
    "plan_code": "lite:year",
    "period": {
        "start_at": "2026-11-12 12:30:18",
        "end_at": "2027-11-12 23:59:59",
    },
    "quota": {
        "total_credits": 4_100_000_000,
        "remaining_credits": 2_700_000_000,
    },
}


def _assert_no_key_leak(tc: unittest.TestCase, text: str, key: str = FIXTURE_KEY) -> None:
    tc.assertNotIn(key, text)
    tc.assertNotIn(key[:12], text)


class _FakeMiMoServer:
    def __init__(self, handler_fn):
        self.handler_fn = handler_fn
        self.requests: list[tuple[str, str, str]] = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                auth = self.headers.get("Authorization", "")
                outer.requests.append(("GET", self.path, auth))
                status, payload = outer.handler_fn(self.path, auth)
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

    def __enter__(self) -> "_FakeMiMoServer":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def _write_fake_secret_store_module(shim_dir: Path, state_file: Path) -> None:
    """Create a D-Bus-free secret_store.py shim in a temp dir for subprocess CLI tests."""
    code = f"""
import json
from pathlib import Path

STATE = Path({str(state_file)!r})

class SecretStoreError(RuntimeError):
    pass

def _load():
    if not STATE.is_file():
        return {{}}
    return json.loads(STATE.read_text(encoding="utf-8"))

def _save(d):
    STATE.write_text(json.dumps(d), encoding="utf-8")

def get(provider, name):
    return _load().get(f"{{provider}}/{{name}}")

def configured(provider, name):
    return bool(get(provider, name))

def set(provider, name, value):
    d = _load()
    d[f"{{provider}}/{{name}}"] = value
    _save(d)

def delete(provider, name):
    d = _load()
    d.pop(f"{{provider}}/{{name}}", None)
    _save(d)
"""
    (shim_dir / "secret_store.py").write_text(code, encoding="utf-8")


class MiMoEnvIsolatedTestCase(unittest.TestCase):
    """Strip any real MiMo/Xiaomi env vars at setup so tests never observe them."""

    def setUp(self) -> None:
        super().setUp()
        self._saved_env: dict[str, str | None] = {}
        for var in ("XIAOMI_API_KEY", "MIMO_API_KEY", "MIMO_API_BASE"):
            self._saved_env[var] = os.environ.pop(var, None)
        self.addCleanup(self._restore_env)

    def _restore_env(self) -> None:
        for var, val in self._saved_env.items():
            if val is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = val


class MiMoNormalizationTests(MiMoEnvIsolatedTestCase):
    """T2 — plan labels, percent formula, period parsing, failure shapes."""

    def test_plan_normalization_table(self) -> None:
        cases = [
            ("lite", "Lite"),
            ("lite:year", "Lite · Annual"),
            ("standard:year", "Standard · Annual"),
            ("pro:month", "Pro · Monthly"),
            ("MAX", "Max"),
            ("ultra:quarter", "ultra:quarter"),
            ("lite:weird", "lite:weird"),
            ("x" * 100, "x" * 64),
            ("", None),
            ("   ", None),
            (None, None),
            (123, None),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_plan(raw), expected)

    def test_percent_calculation_and_clamping(self) -> None:
        provider = MiMoProvider()
        cases = [
            ({"total_credits": 4_100_000_000, "remaining_credits": 2_700_000_000}, 66),
            ({"total_credits": 1000, "remaining_credits": 0}, 0),
            ({"total_credits": 1000, "remaining_credits": 1000}, 100),
            ({"total_credits": 1000, "remaining_credits": 1500}, 100),
            ({"total_credits": 1000, "remaining_credits": -50}, 0),
            ({"total_credits": 4_100_000_000, "used_credits": 1_400_000_000}, 66),
            # Round-half-to-even matching StepFun
            ({"total_credits": 1000, "remaining_credits": 5}, 0),
            ({"total_credits": 1000, "remaining_credits": 995}, 100),
        ]
        for quota, expected_pct in cases:
            with self.subTest(quota=quota):
                out = provider._normalize({"plan_code": "lite:year", "quota": quota})
                self.assertEqual(out["remainingPercent"], expected_pct)
                self.assertEqual(out["meters"][0]["label"], "Credits")
                self.assertEqual(out["meters"][0]["remainingPercent"], expected_pct)

    def test_period_monthly_annual_and_malformed(self) -> None:
        provider = MiMoProvider()
        monthly = provider._normalize(MONTHLY_BODY)
        self.assertEqual(monthly["plan"], "Pro · Monthly")
        self.assertEqual(monthly["resetAt"], "2026-12-11T23:59:59+00:00")
        self.assertEqual(monthly["meters"][0]["resetAt"], "2026-12-11T23:59:59+00:00")
        self.assertEqual(monthly["breakdown"], monthly["meters"])
        self.assertNotIn("secondaryRemainingPercent", monthly)
        self.assertNotIn("auto_renew", monthly)
        self.assertNotIn("claw_enabled", monthly)
        self.assertNotIn("total_credits", json.dumps(monthly))

        annual = provider._normalize(ANNUAL_BODY)
        self.assertEqual(annual["plan"], "Lite · Annual")
        self.assertEqual(annual["resetAt"], "2027-11-12T23:59:59+00:00")
        self.assertEqual(annual["meters"][0]["resetAt"], "2027-11-12T23:59:59+00:00")
        self.assertEqual(len(annual["meters"]), 1)

        malformed = provider._normalize(
            {
                "plan_code": "lite",
                "period": {"end_at": "2026/12/11"},
                "quota": {"total_credits": 100, "remaining_credits": 50},
            }
        )
        self.assertIsNone(malformed["resetAt"])
        self.assertNotIn("resetAt", malformed["meters"][0])
        self.assertEqual(malformed["remainingPercent"], 50)

    def test_invalid_quota_raises_upstream_error(self) -> None:
        provider = MiMoProvider()
        bad_payloads = [
            {"quota": {"total_credits": 0, "remaining_credits": 0}},
            {"quota": {"total_credits": -1, "remaining_credits": 0}},
            {"quota": {"total_credits": True, "remaining_credits": 1}},
            {},
            {"quota": [1, 2, 3]},
            {"quota": {"total_credits": 100}},
        ]
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ProviderError) as ctx:
                    provider._normalize(payload)
                self.assertEqual(ctx.exception.code, "upstream_error")


class MiMoRequestAndIsolationTests(MiMoEnvIsolatedTestCase):
    """T1, T4, T7 — HTTP request, status mapping, URL builder, env/file isolation."""

    def test_url_builder_regions_without_override(self) -> None:
        self.assertEqual(endpoint_url("sgp"), "https://token-plan-sgp.xiaomimimo.com/v1/platform/token_plan")
        self.assertEqual(endpoint_url("cn"), "https://token-plan-cn.xiaomimimo.com/v1/platform/token_plan")
        self.assertEqual(endpoint_url("ams"), "https://token-plan-ams.xiaomimimo.com/v1/platform/token_plan")

    def test_invalid_region_raises_provider_unavailable(self) -> None:
        with self.assertRaises(ProviderError) as ctx:
            MiMoProvider(region="us")
        self.assertEqual(ctx.exception.code, "provider_unavailable")

    def test_key_shape_validation_rejects_bad_values_with_zero_requests(self) -> None:
        self.assertTrue(is_valid_token_plan_key(FIXTURE_KEY))
        for bad in (None, "", "sk-wrong-prefix", "tp-1234", "tp-has space-1234", "tp-has\nnewline", "tp-" + "a" * 260):
            with self.subTest(bad=bad), _FakeMiMoServer(lambda _p, _a: (200, MONTHLY_BODY)) as srv:
                os.environ["MIMO_API_BASE"] = srv.url
                with mock.patch("providers.mimo.secret_get", return_value=bad):
                    p = MiMoProvider(region="sgp")
                    with self.assertRaises(ProviderError) as ctx:
                        p.fetch_usage()
                self.assertEqual(ctx.exception.code, "auth_unavailable")
                self.assertEqual(srv.requests, [])
                if isinstance(bad, str) and len(bad) >= 12:
                    self.assertNotIn(bad[:12], ctx.exception.message)

    def test_secret_store_error_gives_auth_unavailable(self) -> None:
        with mock.patch("providers.mimo.secret_get", side_effect=SecretStoreError("wallet locked")):
            p = MiMoProvider()
            with self.assertRaises(ProviderError) as ctx:
                p.detect()
        self.assertEqual(ctx.exception.code, "auth_unavailable")
        self.assertIn("Credential store unavailable:", ctx.exception.message)

    def test_200_and_401_and_upstream_errors(self) -> None:
        # 200 OK
        with _FakeMiMoServer(lambda _p, _a: (200, ANNUAL_BODY)) as srv:
            os.environ["MIMO_API_BASE"] = srv.url
            with mock.patch("providers.mimo.secret_get", return_value=FIXTURE_KEY):
                out = MiMoProvider(region="sgp").fetch_usage()
            self.assertEqual(out["status"], "ok")
            self.assertEqual(out["plan"], "Lite · Annual")
            self.assertEqual(srv.requests, [("GET", TOKEN_PLAN_PATH, f"Bearer {FIXTURE_KEY}")])
            _assert_no_key_leak(self, json.dumps(out))

        # 401 -> auth_unavailable naming region, exactly 1 request
        with _FakeMiMoServer(lambda _p, _a: (401, {"error": "unauthorized"})) as srv:
            os.environ["MIMO_API_BASE"] = srv.url
            with mock.patch("providers.mimo.secret_get", return_value=FIXTURE_KEY):
                with self.assertRaises(ProviderError) as ctx:
                    MiMoProvider(region="ams").fetch_usage()
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertIn("ams", ctx.exception.message)
            self.assertEqual(len(srv.requests), 1)
            _assert_no_key_leak(self, ctx.exception.message)

        # 403, 500, invalid JSON, JSON array -> upstream_error
        for label, status, body in [
            ("403", 403, b'{"error":"forbidden"}'),
            ("500", 500, b'{"error":"server"}'),
            ("invalid_json", 200, b"<html>bad</html>"),
            ("json_array", 200, b"[1, 2, 3]"),
        ]:
            with self.subTest(case=label), _FakeMiMoServer(lambda _p, _a, s=status, b=body: (s, b)) as srv:
                os.environ["MIMO_API_BASE"] = srv.url
                with mock.patch("providers.mimo.secret_get", return_value=FIXTURE_KEY):
                    with self.assertRaises(ProviderError) as ctx:
                        MiMoProvider(region="sgp").fetch_usage()
                self.assertEqual(ctx.exception.code, "upstream_error")
                _assert_no_key_leak(self, ctx.exception.message)

        # Closed port -> URLError -> upstream_error
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        closed_port = sock.getsockname()[1]
        sock.close()
        os.environ["MIMO_API_BASE"] = f"http://127.0.0.1:{closed_port}"
        with mock.patch("providers.mimo.secret_get", return_value=FIXTURE_KEY):
            with self.assertRaises(ProviderError) as ctx:
                MiMoProvider().fetch_usage()
        self.assertEqual(ctx.exception.code, "upstream_error")

        # Timeout -> upstream_error
        with mock.patch("providers.mimo.secret_get", return_value=FIXTURE_KEY):
            with mock.patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
                with self.assertRaises(ProviderError) as ctx:
                    MiMoProvider().fetch_usage()
        self.assertEqual(ctx.exception.code, "upstream_error")

    def test_t4_env_vars_ignored_and_no_forbidden_files_opened(self) -> None:
        os.environ["XIAOMI_API_KEY"] = "tp-env-should-not-be-used"
        os.environ["MIMO_API_KEY"] = "tp-env-should-not-be-used"

        # 1. Empty store + env vars set -> auth_unavailable, zero requests
        with _FakeMiMoServer(lambda _p, _a: (200, ANNUAL_BODY)) as srv:
            os.environ["MIMO_API_BASE"] = srv.url
            with mock.patch("providers.mimo.secret_get", return_value=None):
                with self.assertRaises(ProviderError) as ctx:
                    MiMoProvider().fetch_usage()
            self.assertEqual(ctx.exception.code, "auth_unavailable")
            self.assertEqual(srv.requests, [])

        # 2. Store has FIXTURE_KEY + env vars set -> only FIXTURE_KEY sent; no bashrc/profile/mimocode opened
        opened_paths: list[str] = []
        orig_open = builtins.open
        orig_path_open = Path.open
        orig_read_text = Path.read_text

        def spy_open(file, *args, **kwargs):
            opened_paths.append(str(file))
            return orig_open(file, *args, **kwargs)

        def spy_path_open(self_p, *args, **kwargs):
            opened_paths.append(str(self_p))
            return orig_path_open(self_p, *args, **kwargs)

        def spy_read_text(self_p, *args, **kwargs):
            opened_paths.append(str(self_p))
            return orig_read_text(self_p, *args, **kwargs)

        with _FakeMiMoServer(lambda _p, _a: (200, ANNUAL_BODY)) as srv:
            os.environ["MIMO_API_BASE"] = srv.url
            with (
                mock.patch("providers.mimo.secret_get", return_value=FIXTURE_KEY),
                mock.patch("builtins.open", side_effect=spy_open),
                mock.patch.object(Path, "open", spy_path_open),
                mock.patch.object(Path, "read_text", spy_read_text),
            ):
                out = MiMoProvider().fetch_usage()
            self.assertEqual(out["status"], "ok")
            self.assertEqual(srv.requests, [("GET", TOKEN_PLAN_PATH, f"Bearer {FIXTURE_KEY}")])

        for p in opened_paths:
            low = p.lower()
            self.assertNotIn("bashrc", low)
            self.assertNotIn(".profile", low)
            self.assertNotIn("mimocode", low)


class MiMoCLISubprocessTests(MiMoEnvIsolatedTestCase):
    """T3 & T7 — subprocess ai-usage status/auth/cache tests with D-Bus-free secret_store shim."""

    def _run_cli(
        self,
        args: list[str],
        *,
        shim_dir: Path,
        api_base: str,
        cache_home: Path,
        stdin_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(shim_dir) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["MIMO_API_BASE"] = api_base
        env["XDG_CACHE_HOME"] = str(cache_home)
        env.pop("XIAOMI_API_KEY", None)
        env.pop("MIMO_API_KEY", None)
        return subprocess.run(
            [sys.executable, str(COLLECTOR / "ai-usage"), *args],
            input=stdin_text,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_status_auth_region_and_cache_flows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shim_dir = root / "shim"
            shim_dir.mkdir()
            state_file = root / "store.json"
            cache_home = root / "cache"
            _write_fake_secret_store_module(shim_dir, state_file)

            mode = {"status": 200, "body": ANNUAL_BODY}

            def handler(_path: str, _auth: str):
                return mode["status"], mode["body"]

            with _FakeMiMoServer(handler) as srv:
                # 1. auth status on empty store -> missing
                r = self._run_cli(["auth", "mimo", "status"], shim_dir=shim_dir, api_base=srv.url, cache_home=cache_home)
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout.strip(), "missing")

                # 2. auth set with invalid key -> invalid, stores nothing
                r = self._run_cli(
                    ["auth", "mimo", "set"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                    stdin_text="not-a-key\n",
                )
                self.assertEqual(r.returncode, 1)
                self.assertEqual(r.stdout.strip(), "invalid")
                self.assertFalse(state_file.exists())

                # 3. auth set with valid key -> working
                r = self._run_cli(
                    ["auth", "mimo", "set", "--region", "sgp"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                    stdin_text=FIXTURE_KEY + "\n",
                )
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout.strip(), "working")
                _assert_no_key_leak(self, r.stdout + r.stderr)

                # 4. status mimo --json (populates cache)
                r = self._run_cli(
                    ["status", "mimo", "--json", "--region", "sgp"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                )
                self.assertEqual(r.returncode, 0)
                data = json.loads(r.stdout)
                self.assertEqual(data["status"], "ok")
                self.assertEqual(data["plan"], "Lite · Annual")
                self.assertEqual(data["meters"][0]["label"], "Credits")
                _assert_no_key_leak(self, r.stdout + r.stderr)

                cache_file = cache_home / "horizon" / "usage-mimo.json"
                self.assertTrue(cache_file.is_file())
                _assert_no_key_leak(self, cache_file.read_text(encoding="utf-8"))

                # 5. --region us rejected by argparse (exit 2, no request)
                before = len(srv.requests)
                r = self._run_cli(
                    ["status", "mimo", "--json", "--region", "us"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                )
                self.assertEqual(r.returncode, 2)
                self.assertEqual(len(srv.requests), before)

                # 6. 401 on --region cn names cn in error; auth set prints auth_failed
                mode["status"] = 401
                mode["body"] = {"error": "unauthorized"}
                r = self._run_cli(
                    ["status", "mimo", "--json", "--no-cache", "--region", "cn"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                )
                self.assertEqual(r.returncode, 1)
                err_data = json.loads(r.stdout)
                self.assertEqual(err_data["status"], "auth_unavailable")
                self.assertIn("cn", err_data["error"])
                self.assertNotIn("meters", err_data)
                _assert_no_key_leak(self, r.stdout + r.stderr)

                r = self._run_cli(
                    ["auth", "mimo", "set", "--region", "cn"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                    stdin_text=FIXTURE_KEY + "\n",
                )
                self.assertEqual(r.returncode, 1)
                self.assertEqual(r.stdout.strip(), "auth_failed")

                # 7. 500 -> auth set prints unavailable; warm cache status gives stale
                mode["status"] = 500
                mode["body"] = {"error": "down"}
                r = self._run_cli(
                    ["auth", "mimo", "set"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                    stdin_text=FIXTURE_KEY + "\n",
                )
                self.assertEqual(r.returncode, 1)
                self.assertEqual(r.stdout.strip(), "unavailable")

                r = self._run_cli(
                    ["status", "mimo", "--json"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                )
                self.assertEqual(r.returncode, 1)
                stale_data = json.loads(r.stdout)
                self.assertEqual(stale_data["status"], "stale")
                self.assertTrue(stale_data["stale"])
                self.assertEqual(stale_data["meters"][0]["label"], "Credits")
                _assert_no_key_leak(self, r.stdout + r.stderr)

                # 8. Cold cache + total_credits=0 -> upstream_error with no meters
                mode["status"] = 200
                mode["body"] = {"quota": {"total_credits": 0, "remaining_credits": 0}}
                r = self._run_cli(
                    ["status", "mimo", "--json", "--no-cache"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                )
                self.assertEqual(r.returncode, 1)
                cold_err = json.loads(r.stdout)
                self.assertEqual(cold_err["status"], "upstream_error")
                self.assertNotIn("meters", cold_err)

                # 9. auth clear -> cleared
                r = self._run_cli(
                    ["auth", "mimo", "clear"],
                    shim_dir=shim_dir,
                    api_base=srv.url,
                    cache_home=cache_home,
                )
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout.strip(), "cleared")


if __name__ == "__main__":
    unittest.main()
