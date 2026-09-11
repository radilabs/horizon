"""Unit tests for bounded StepFun Oasis refresh (no live secrets)."""

from __future__ import annotations

import base64
import json
import sys
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / "collector"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers import ProviderError  # noqa: E402
from providers.stepfun import (  # noqa: E402
    StepFunProvider,
    combine_oasis_token_from_refresh,
)


def _b64(obj: dict) -> str:
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def fake_jwt(**claims) -> str:
    return f"{_b64({'alg': 'none'})}.{_b64(claims)}.sig"


def pair(access_claims=None, refresh_claims=None) -> str:
    access = fake_jwt(**(access_claims or {"exp": 1}))
    refresh = fake_jwt(**(refresh_claims or {"device_id": "dev-1", "app_id": 20700, "exp": 1}))
    return f"{access}...{refresh}"


USAGE_OK = {
    "status": 1,
    "plan_family": 1,
    "five_hour_usage_left_rate": 0.5,
    "weekly_usage_left_rate": 0.8,
    "five_hour_usage_reset_time": "1786399200",
    "weekly_usage_reset_time": "1786564800",
}

PLAN_OK = {"status": 1, "subscription": {"name": "Plus"}}

NEW_ACCESS = fake_jwt(exp=9999999999)
NEW_REFRESH = fake_jwt(device_id="dev-1", app_id=20700, exp=9999999999)
REFRESH_OK = {
    "accessToken": {"raw": NEW_ACCESS, "duration": 3600, "mode": 1},
    "refreshToken": {"raw": NEW_REFRESH},
}


class FakeHTTP:
    def __init__(self, script: list[tuple[str, int, dict | bytes]]):
        self.script = list(script)
        self.calls: list[str] = []

    def __call__(self, req, timeout=30):  # noqa: ANN001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        self.calls.append(url)
        if not self.script:
            raise AssertionError(f"unexpected request: {url}")
        needle, status, payload = self.script.pop(0)
        if needle not in url:
            raise AssertionError(f"expected {needle} in {url}")
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


class CombineTests(unittest.TestCase):
    def test_pair_from_nested_raw(self) -> None:
        combined = combine_oasis_token_from_refresh(REFRESH_OK)
        self.assertEqual(combined, f"{NEW_ACCESS}...{NEW_REFRESH}")

    def test_malformed_empty(self) -> None:
        self.assertIsNone(combine_oasis_token_from_refresh({"foo": 1}))


class RefreshFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.token = pair()
        self.store = {"stepfun/oasis-token": self.token}

        def fake_get(provider: str, name: str) -> str | None:
            return self.store.get(f"{provider}/{name}")

        def fake_set(provider: str, name: str, value: str) -> None:
            self.store[f"{provider}/{name}"] = value
            self.last_set = value

        self.last_set = None
        get_p = mock.patch("providers.stepfun.secret_get", side_effect=fake_get)
        set_p = mock.patch("providers.stepfun.secret_set", side_effect=fake_set)
        self.addCleanup(get_p.stop)
        self.addCleanup(set_p.stop)
        get_p.start()
        set_p.start()

    def test_valid_token_does_not_refresh(self) -> None:
        http = FakeHTTP(
            [
                ("QueryStepPlanRateLimit", 200, USAGE_OK),
                ("GetStepPlanStatus", 200, PLAN_OK),
            ]
        )
        with mock.patch("urllib.request.urlopen", http):
            out = StepFunProvider().fetch_usage()
        self.assertEqual(out["status"], "ok")
        self.assertIsNone(self.last_set)
        self.assertEqual(self.store["stepfun/oasis-token"], self.token)

    def test_refresh_success_validates_before_store(self) -> None:
        order: list[str] = []
        orig_set = self.store

        def tracking_set(provider: str, name: str, value: str) -> None:
            order.append("set")
            orig_set[f"{provider}/{name}"] = value
            self.last_set = value

        with mock.patch("providers.stepfun.secret_set", side_effect=tracking_set):
            http = FakeHTTP(
                [
                    ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
                    ("RefreshToken", 200, REFRESH_OK),
                    ("QueryStepPlanRateLimit", 200, USAGE_OK),
                    ("QueryStepPlanRateLimit", 200, USAGE_OK),
                    ("GetStepPlanStatus", 200, PLAN_OK),
                ]
            )

            def wrapped(req, timeout=30):  # noqa: ANN001
                url = req.full_url if hasattr(req, "full_url") else str(req)
                if "RefreshToken" in url:
                    order.append("refresh")
                elif "QueryStepPlanRateLimit" in url:
                    order.append("usage")
                return http(req, timeout=timeout)

            with mock.patch("urllib.request.urlopen", wrapped):
                out = StepFunProvider().fetch_usage()
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["plan"], "Plus")
        self.assertIsNotNone(self.last_set)
        self.assertNotEqual(self.last_set, self.token)
        # validate usage happens before set
        self.assertEqual(order[:3], ["usage", "refresh", "usage"])
        self.assertIn("set", order)
        self.assertLess(order.index("refresh"), order.index("set"))
        self.assertLess(order.index("usage", 1), order.index("set"))

    def test_refresh_http_failure_keeps_store(self) -> None:
        http = FakeHTTP(
            [
                ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
                ("RefreshToken", 401, {"message": "unauthorized"}),
            ]
        )
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as ctx:
                StepFunProvider().fetch_usage()
        self.assertEqual(ctx.exception.code, "auth_unavailable")
        self.assertIsNone(self.last_set)
        self.assertEqual(self.store["stepfun/oasis-token"], self.token)
        self.assertTrue(any("RefreshToken" in c for c in http.calls))
        self.assertEqual(sum(1 for c in http.calls if "RefreshToken" in c), 1)

    def test_malformed_refresh_keeps_store(self) -> None:
        http = FakeHTTP(
            [
                ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
                ("RefreshToken", 200, {"nope": True}),
            ]
        )
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as ctx:
                StepFunProvider().fetch_usage()
        self.assertEqual(ctx.exception.code, "auth_unavailable")
        self.assertIsNone(self.last_set)
        self.assertEqual(self.store["stepfun/oasis-token"], self.token)

    def test_validate_failure_keeps_store(self) -> None:
        http = FakeHTTP(
            [
                ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
                ("RefreshToken", 200, REFRESH_OK),
                ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
            ]
        )
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as ctx:
                StepFunProvider().fetch_usage()
        self.assertEqual(ctx.exception.code, "auth_unavailable")
        self.assertIsNone(self.last_set)
        self.assertEqual(self.store["stepfun/oasis-token"], self.token)

    def test_second_auth_failure_does_not_refresh_again(self) -> None:
        http = FakeHTTP(
            [
                ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
                ("RefreshToken", 200, REFRESH_OK),
                ("QueryStepPlanRateLimit", 200, USAGE_OK),
                ("QueryStepPlanRateLimit", 401, {"message": "unauthorized"}),
            ]
        )
        with mock.patch("urllib.request.urlopen", http):
            with self.assertRaises(ProviderError) as ctx:
                StepFunProvider().fetch_usage()
        self.assertEqual(ctx.exception.code, "auth_unavailable")
        self.assertEqual(sum(1 for c in http.calls if "RefreshToken" in c), 1)


if __name__ == "__main__":
    unittest.main()
