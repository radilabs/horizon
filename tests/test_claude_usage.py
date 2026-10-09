"""Unit tests for read-only Claude usage (no live secrets)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "collector"
if str(COLLECTOR) not in sys.path:
    sys.path.insert(0, str(COLLECTOR))

from providers import ProviderError  # noqa: E402
from providers.claude import ClaudeProvider  # noqa: E402

FUTURE_MS = int((time.time() + 3600) * 1000)
PAST_MS = int((time.time() - 3600) * 1000)

USAGE_OK = {
    "five_hour": {
        "utilization": 1.0,
        "resets_at": "2026-10-09T13:59:59+00:00",
    },
    "seven_day": {
        "utilization": 22.0,
        "resets_at": "2026-10-12T01:59:59+00:00",
    },
    "seven_day_opus": None,
    "seven_day_sonnet": None,
    "extra_usage": {"is_enabled": False, "utilization": None},
    "limits": [
        {"kind": "session", "percent": 1},
        {"kind": "weekly_all", "percent": 22},
    ],
    "spend": {"enabled": False, "percent": 0},
    "seven_day_breakdown": {
        "rows": [{"key": "claude_code", "display_name": "Claude Code", "percent": 93}]
    },
}


def credentials(**oauth) -> dict:
    body = {
        "accessToken": "sk-ant-test-access",
        "refreshToken": "sk-ant-test-refresh",
        "expiresAt": FUTURE_MS,
        "subscriptionType": "pro",
    }
    body.update(oauth)
    return {"claudeAiOauth": body}


class FakeHTTP:
    def __init__(self, script: list[tuple[int, dict | bytes]]):
        self.script = list(script)
        self.calls: list[tuple[str, str, dict[str, str]]] = []

    def __call__(self, req, timeout=30):  # noqa: ANN001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        method = getattr(req, "method", "GET") or "GET"
        headers = {k.lower(): v for k, v in req.header_items()}
        self.calls.append((method, url, headers))
        if not self.script:
            raise AssertionError(f"unexpected request: {url}")
        status, payload = self.script.pop(0)
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        if status != 200:
            raise urllib.error.HTTPError(url, status, "err", hdrs=None, fp=BytesIO(body))

        class Resp:
            def __init__(self, data: bytes, code: int):
                self._data = data
                self.status = code

            def read(self) -> bytes:
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return Resp(body, status)


class ClaudeUsageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.tmp = Path(self._dir.name) / ".credentials.json"

    def _write(self, payload: dict) -> None:
        self.tmp.write_text(json.dumps(payload))
        os.chmod(self.tmp, 0o600)

    def _provider(self) -> ClaudeProvider:
        return ClaudeProvider(credentials_path=self.tmp)

    def test_normalizes_live_window_shape(self) -> None:
        self._write(credentials())
        http = FakeHTTP([(200, USAGE_OK)])
        with mock.patch("urllib.request.urlopen", http):
            out = self._provider().fetch_usage()
        self.assertEqual(out["provider"], "claude")
        self.assertEqual(out["displayName"], "Claude")
        self.assertEqual(out["plan"], "Pro")
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["remainingPercent"], 99)
        self.assertEqual(out["secondaryRemainingPercent"], 78)
        self.assertEqual(out["resetAt"], "2026-10-09T13:59:59+00:00")
        self.assertEqual(
            out["breakdown"],
            [
                {
                    "label": "Current session",
                    "remainingPercent": 99,
                    "resetAt": "2026-10-09T13:59:59+00:00",
                },
                {
                    "label": "Current week (all models)",
                    "remainingPercent": 78,
                    "resetAt": "2026-10-12T01:59:59+00:00",
                },
            ],
        )
        self.assertNotIn("limits", json.dumps(out))
        self.assertNotIn("sk-ant", json.dumps(out))

    def test_includes_model_windows_and_enabled_extra_usage(self) -> None:
        self._write(credentials(subscriptionType="max"))
        payload = {
            "five_hour": {"utilization": 10, "resets_at": "2026-10-09T13:00:00+00:00"},
            "seven_day": {"utilization": 20, "resets_at": "2026-10-12T01:00:00+00:00"},
            "seven_day_opus": {"utilization": 40, "resets_at": "2026-10-12T01:00:00+00:00"},
            "seven_day_sonnet": {"utilization": 5, "resets_at": "2026-10-12T01:00:00+00:00"},
            "tangelo": {"utilization": 3, "resets_at": "2026-10-12T01:00:00+00:00", "label": "Tangelo credit"},
            "extra_usage": {"is_enabled": True, "utilization": 50, "resets_at": "2026-11-01T00:00:00+00:00"},
        }
        http = FakeHTTP([(200, payload)])
        with mock.patch("urllib.request.urlopen", http):
            out = self._provider().fetch_usage()
        labels = [row["label"] for row in out["breakdown"]]
        self.assertEqual(
            labels,
            [
                "Current session",
                "Current week (all models)",
                "Opus limit",
                "Current week (Sonnet only)",
                "Tangelo credit",
                "Extra usage",
            ],
        )
        self.assertEqual(out["plan"], "Max")
        self.assertEqual(out["breakdown"][-1]["remainingPercent"], 50)

    def test_missing_file_is_auth_unavailable(self) -> None:
        missing = self.tmp.with_suffix(".missing")
        provider = ClaudeProvider(credentials_path=missing)
        with self.assertRaises(ProviderError) as caught:
            provider.fetch_usage()
        self.assertEqual(caught.exception.code, "auth_unavailable")
        self.assertIn("Re-authenticate in Claude Code", caught.exception.message)
        self.assertFalse(missing.exists())

    def test_expired_session_does_not_call_network_or_refresh(self) -> None:
        self._write(credentials(expiresAt=PAST_MS))
        before = self.tmp.read_bytes()
        http = FakeHTTP([(200, USAGE_OK)])
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as caught:
                self._provider().fetch_usage(force_refresh=True)
        self.assertEqual(caught.exception.code, "auth_unavailable")
        self.assertIn("expired", caught.exception.message)
        self.assertEqual(http.calls, [])
        self.assertEqual(self.tmp.read_bytes(), before)

    def test_rejected_credential_is_auth_unavailable_and_file_unchanged(self) -> None:
        self._write(credentials())
        before = self.tmp.read_bytes()
        http = FakeHTTP([(401, {"error": "unauthorized"})])
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as caught:
                self._provider().fetch_usage()
        self.assertEqual(caught.exception.code, "auth_unavailable")
        self.assertIn("HTTP 401", caught.exception.message)
        self.assertEqual(len(http.calls), 1)
        method, url, headers = http.calls[0]
        self.assertEqual(method, "GET")
        self.assertTrue(url.endswith("/api/oauth/usage"))
        self.assertNotIn("oauth/token", url)
        self.assertIn("sk-ant-test-access", headers.get("authorization", ""))
        self.assertNotIn("sk-ant-test-refresh", headers.get("authorization", ""))
        self.assertNotIn("refresh", json.dumps(headers))
        self.assertEqual(self.tmp.read_bytes(), before)

    def test_forbidden_credential_is_auth_unavailable(self) -> None:
        self._write(credentials())
        before = self.tmp.read_bytes()
        http = FakeHTTP([(403, {"error": "forbidden"})])
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as caught:
                self._provider().fetch_usage()
        self.assertEqual(caught.exception.code, "auth_unavailable")
        self.assertIn("HTTP 403", caught.exception.message)
        self.assertEqual(self.tmp.read_bytes(), before)

    def test_upstream_failure(self) -> None:
        self._write(credentials())
        http = FakeHTTP([(500, b"nope")])
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as caught:
                self._provider().fetch_usage()
        self.assertEqual(caught.exception.code, "upstream_error")
        self.assertEqual(len(http.calls), 1)

    def test_one_request_per_fetch(self) -> None:
        self._write(credentials())
        http = FakeHTTP([(200, USAGE_OK), (200, USAGE_OK)])
        provider = self._provider()
        with mock.patch("urllib.request.urlopen", http):
            provider.fetch_usage(force_refresh=True)
        self.assertEqual(len(http.calls), 1)

    def test_cli_missing_auth_json(self) -> None:
        missing = self.tmp.with_suffix(".cli-missing")
        proc = subprocess.run(
            [
                sys.executable,
                str(COLLECTOR / "ai-usage"),
                "status",
                "claude",
                "--json",
                "--no-cache",
                "--auth-file",
                str(missing),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["provider"], "claude")
        self.assertEqual(payload["status"], "auth_unavailable")
        self.assertNotIn("sk-", proc.stdout + proc.stderr)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
