"""Deterministic Phase 7 contract tests. No live network and no secrets."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "collector"
if str(COLLECTOR) not in sys.path:
    sys.path.insert(0, str(COLLECTOR))

from cache import stale_payload, write_success  # noqa: E402
from providers import ProviderError, error_payload  # noqa: E402
from providers.claude import (  # noqa: E402
    ClaudeProvider,
    _expired as claude_expired,
    _remaining_from_used as claude_remaining_from_used,
    _utilization as claude_utilization,
)
from providers.codex import CodexProvider, _meter_from_window as codex_meter_from_window  # noqa: E402
from providers.contract import meters_from_payload, project_ok  # noqa: E402
from providers.cursor import CursorProvider  # noqa: E402
from providers.stepfun import StepFunProvider  # noqa: E402

SECRET_MARKERS = ("sk-ant-", "access_token", "refresh_token", "Bearer ", "eyJ")


class ContractProjectionTests(unittest.TestCase):
    def test_projection_matches_meters_and_keeps_compat_fields(self) -> None:
        payload = project_ok(
            provider="example",
            display_name="Example",
            plan="Pro",
            meters=[
                {"label": "Session", "remainingPercent": 99, "resetAt": "2026-10-09T14:00:00+00:00"},
                {"label": "Week", "remainingPercent": 78, "resetAt": "2026-10-12T02:00:00+00:00"},
                {"label": "Opus", "remainingPercent": 40, "resetAt": "2026-10-12T02:00:00+00:00"},
            ],
        )
        self.assertEqual(payload["meters"], payload["breakdown"])
        self.assertEqual(payload["remainingPercent"], 99)
        self.assertEqual(payload["resetAt"], "2026-10-09T14:00:00+00:00")
        self.assertEqual(payload["secondaryRemainingPercent"], 78)
        self.assertEqual(len(payload["meters"]), 3)
        self.assertNotIn("usedPercent", payload)
        self.assertNotIn("usedPercent", payload["meters"][0])

    def test_legacy_payload_without_meters_still_reads(self) -> None:
        legacy = {
            "remainingPercent": 94,
            "resetAt": "2026-08-17T12:00:00+02:00",
            "secondaryRemainingPercent": 80,
        }
        meters = meters_from_payload(legacy)
        self.assertEqual(meters[0]["remainingPercent"], 94)
        self.assertEqual(meters[1]["remainingPercent"], 80)
        self.assertEqual(meters[0]["label"], "Usage limit")
        self.assertEqual(meters[1]["label"], "Usage limit")
        self.assertEqual(meters[0]["resetAt"], "2026-08-17T12:00:00+02:00")
        self.assertNotIn("resetAt", meters[1])

    def test_error_payload_has_no_meters_or_fabricated_quota(self) -> None:
        payload = error_payload("claude", "Claude", "auth_unavailable", "Re-authenticate in Claude Code.")
        self.assertNotIn("meters", payload)
        self.assertIsNone(payload["remainingPercent"])
        self.assertIsNone(payload["resetAt"])
        self.assertIsNone(payload["plan"])
        self.assertEqual(payload["status"], "auth_unavailable")
        self.assertEqual(
            set(payload),
            {"provider", "displayName", "plan", "remainingPercent", "resetAt", "status", "error"},
        )


class CodexContractTests(unittest.TestCase):
    def test_weekly_primary_and_five_hour_secondary_keep_own_resets(self) -> None:
        weekly_reset = 1_780_000_000
        session_reset = 1_780_010_000
        out = CodexProvider()._normalize(
            {
                "plan_type": "plus",
                "rate_limit": {
                    "primary_window": {
                        "used_percent": 6,
                        "limit_window_seconds": 604800,
                        "reset_at": weekly_reset,
                    },
                    "secondary_window": {
                        "used_percent": 20,
                        "limit_window_seconds": 18000,
                        "reset_at": session_reset,
                    },
                },
            }
        )
        labels = [meter["label"] for meter in out["meters"]]
        self.assertEqual(labels, ["Weekly limit", "5-hour limit"])
        self.assertNotIn("Primary", labels)
        self.assertNotIn("Secondary", labels)
        self.assertEqual(out["remainingPercent"], 94)
        self.assertEqual(out["secondaryRemainingPercent"], 80)
        self.assertEqual(out["meters"], out["breakdown"])
        self.assertEqual(datetime.fromisoformat(out["meters"][0]["resetAt"]).timestamp(), weekly_reset)
        self.assertEqual(datetime.fromisoformat(out["meters"][1]["resetAt"]).timestamp(), session_reset)
        self.assertNotEqual(out["meters"][0]["resetAt"], out["meters"][1]["resetAt"])

    def test_missing_window_length_does_not_invent_primary_name(self) -> None:
        out = CodexProvider()._normalize(
            {
                "plan_type": "plus",
                "rate_limit": {"primary_window": {"used_percent": 1, "reset_at": 1_780_000_000}},
            }
        )
        self.assertEqual(out["meters"][0]["label"], "Usage limit")
        self.assertNotIn("secondaryRemainingPercent", out)

    def test_one_day_is_not_labeled_as_twenty_four_hours(self) -> None:
        out = CodexProvider()._normalize(
            {
                "plan_type": "plus",
                "rate_limit": {
                    "primary_window": {
                        "used_percent": 0,
                        "limit_window_seconds": 86400,
                        "reset_at": 1_780_000_000,
                    },
                    "secondary_window": {
                        "used_percent": 5,
                        "limit_window_seconds": 18000,
                        "reset_at": 1_780_001_000,
                    },
                },
            }
        )
        self.assertEqual([meter["label"] for meter in out["meters"]], ["1-day limit", "5-hour limit"])

    def test_duplicate_duration_labels_stay_in_order(self) -> None:
        out = CodexProvider()._normalize(
            {
                "plan_type": "plus",
                "rate_limit": {
                    "primary_window": {
                        "used_percent": 1,
                        "limit_window_seconds": 18000,
                        "reset_at": 1_780_000_000,
                    },
                    "secondary_window": {
                        "used_percent": 2,
                        "limit_window_seconds": 18000,
                        "reset_at": 1_780_002_000,
                    },
                },
            }
        )
        self.assertEqual([meter["label"] for meter in out["meters"]], ["5-hour limit", "5-hour limit"])
        self.assertEqual(out["meters"][0]["remainingPercent"], 99)
        self.assertEqual(out["meters"][1]["remainingPercent"], 98)


class CursorContractTests(unittest.TestCase):
    def test_two_pools_ignore_included_spend_aggregate(self) -> None:
        out = CursorProvider()._normalize(
            {
                "billingCycleEnd": "1756848242000",
                "planUsage": {
                    "autoPercentUsed": 2,
                    "apiPercentUsed": 40,
                    "totalPercentUsed": 99,
                    "remaining": 10,
                    "limit": 100,
                    "displayMessage": "You've used 90% of your included usage",
                },
            },
            "Pro",
        )
        self.assertEqual(
            [meter["label"] for meter in out["meters"]],
            ["Cursor Models", "Other Models"],
        )
        self.assertEqual(out["meters"][0]["remainingPercent"], 98)
        self.assertEqual(out["meters"][1]["remainingPercent"], 60)
        self.assertEqual(out["secondaryRemainingPercent"], 60)
        self.assertEqual(out["meters"][0]["resetAt"], out["meters"][1]["resetAt"])
        blob = json.dumps(out)
        self.assertNotIn("included", blob.lower())
        self.assertNotIn("displayMessage", blob)


class StepFunContractTests(unittest.TestCase):
    def test_windows_have_independent_resets(self) -> None:
        out = StepFunProvider()._normalize(
            {
                "five_hour_usage_left_rate": 0.84,
                "weekly_usage_left_rate": 0.62,
                "five_hour_usage_reset_time": "1786399200",
                "weekly_usage_reset_time": "1786564800",
            },
            "Plus",
        )
        self.assertEqual(
            [meter["label"] for meter in out["meters"]],
            ["5-Hour Usage", "Weekly Usage"],
        )
        self.assertEqual(out["remainingPercent"], 84)
        self.assertEqual(out["secondaryRemainingPercent"], 62)
        self.assertNotEqual(out["meters"][0]["resetAt"], out["meters"][1]["resetAt"])
        self.assertEqual(out["meters"], out["breakdown"])

    def test_credit_valid_buckets_give_single_credits_meter(self) -> None:
        out = StepFunProvider()._normalize(
            {
                "plan_family": 2,
                "plan_credit_rate_limit": {
                    "credit_buckets": [
                        {"credit_total": 100, "credit_residual": 30},
                        {"credit_total": 300, "credit_residual": 210},
                    ],
                    "subscription_credit_left_rate": 0.1,
                    "topup_credit_left_rate": 0.9,
                    "subscription_credit_reset_time": "1786564800",
                },
            },
            "Step Plan",
        )
        self.assertEqual(len(out["meters"]), 1)
        self.assertEqual(out["meters"][0]["label"], "Credits")
        # (30 + 210) / (100 + 300) = 240 / 400 = 0.60 -> 60%
        self.assertEqual(out["meters"][0]["remainingPercent"], 60)
        self.assertIn("resetAt", out["meters"][0])

    def test_credit_no_buckets_subscription_rate_gives_subscription_credits(self) -> None:
        out = StepFunProvider()._normalize(
            {
                "plan_family": 2,
                "plan_credit_rate_limit": {
                    "subscription_credit_left_rate": 0.42,
                    "subscription_credit_reset_time": "1786564800",
                },
            },
            "Step Plan",
        )
        self.assertEqual(len(out["meters"]), 1)
        self.assertEqual(out["meters"][0]["label"], "Subscription Credits")
        self.assertEqual(out["meters"][0]["remainingPercent"], 42)
        self.assertIn("resetAt", out["meters"][0])
        self.assertNotEqual(out["meters"][0]["label"], "Credits")

    def test_credit_no_buckets_only_topup_gives_topup_credits(self) -> None:
        out = StepFunProvider()._normalize(
            {
                "plan_family": 2,
                "plan_credit_rate_limit": {
                    "topup_credit_left_rate": 0.75,
                },
            },
            "Step Plan",
        )
        self.assertEqual(len(out["meters"]), 1)
        self.assertEqual(out["meters"][0]["label"], "Top-up Credits")
        self.assertEqual(out["meters"][0]["remainingPercent"], 75)
        self.assertNotIn("resetAt", out["meters"][0])

    def test_credit_invalid_buckets_falls_back_to_subscription_credits(self) -> None:
        out = StepFunProvider()._normalize(
            {
                "plan_family": 2,
                "plan_credit_rate_limit": {
                    "credit_buckets": [
                        {"credit_total": 0, "credit_residual": 10},
                    ],
                    "subscription_credit_left_rate": 0.55,
                    "subscription_credit_reset_time": "1786564800",
                },
            },
            "Step Plan",
        )
        self.assertEqual(len(out["meters"]), 1)
        self.assertEqual(out["meters"][0]["label"], "Subscription Credits")
        self.assertEqual(out["meters"][0]["remainingPercent"], 55)

    def test_credit_separate_rates_are_never_summed(self) -> None:
        out = StepFunProvider()._normalize(
            {
                "plan_family": 2,
                "plan_credit_rate_limit": {
                    "subscription_credit_left_rate": 0.4,
                    "topup_credit_left_rate": 0.5,
                    "subscription_credit_reset_time": "1786564800",
                },
            },
            "Step Plan",
        )
        self.assertEqual(len(out["meters"]), 1)
        self.assertEqual(out["meters"][0]["label"], "Subscription Credits")
        self.assertEqual(out["meters"][0]["remainingPercent"], 40)
        self.assertNotEqual(out["meters"][0]["remainingPercent"], 90)


class ClaudeContractTests(unittest.TestCase):
    def test_utilization_is_percent_used_and_extra_windows_stay_meters(self) -> None:
        out = ClaudeProvider()._normalize(
            {
                "five_hour": {"utilization": 1.0, "resets_at": "2026-10-09T13:59:59+00:00"},
                "seven_day": {"utilization": 22.0, "resets_at": "2026-10-12T01:59:59+00:00"},
                "seven_day_opus": {"utilization": 10.0, "resets_at": "2026-10-12T01:59:59+00:00"},
                "seven_day_breakdown": {"Claude Code": 93, "Chats": 7},
                "spend": {"is_enabled": False, "utilization": 4},
                "extra_usage": {"is_enabled": False, "utilization": 50},
            },
            "Pro",
        )
        self.assertEqual(out["meters"][0]["remainingPercent"], 99)
        self.assertEqual(out["meters"][1]["remainingPercent"], 78)
        self.assertEqual(out["meters"][2]["label"], "Opus limit")
        self.assertEqual(out["meters"][2]["remainingPercent"], 90)
        self.assertEqual(len(out["meters"]), 3)
        self.assertEqual(out["secondaryRemainingPercent"], 78)
        labels = [meter["label"] for meter in out["meters"]]
        self.assertNotIn("Claude Code", labels)
        self.assertNotIn("Extra usage", labels)

    def test_auth_failure_does_not_invent_meters(self) -> None:
        payload = error_payload("claude", "Claude", "upstream_error", "Claude usage failed (HTTP 500)")
        self.assertNotIn("meters", payload)
        self.assertEqual(meters_from_payload(payload), [])


class CacheContractTests(unittest.TestCase):
    def test_cache_round_trip_keeps_meters_and_stale_state(self) -> None:
        payload = project_ok(
            provider="claude",
            display_name="Claude",
            plan="Pro",
            meters=[
                {"label": "Current session", "remainingPercent": 99, "resetAt": "2026-10-09T14:00:00+00:00"},
                {"label": "Current week (all models)", "remainingPercent": 78, "resetAt": "2026-10-12T02:00:00+00:00"},
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = tmp
            try:
                write_success("claude", payload)
                stale = stale_payload("claude", "Claude", "Current refresh failed")
            finally:
                if old is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old
        self.assertIsNotNone(stale)
        assert stale is not None
        self.assertEqual(stale["status"], "stale")
        self.assertTrue(stale["stale"])
        self.assertEqual(stale["meters"][1]["label"], "Current week (all models)")
        self.assertEqual(stale["meters"], stale["breakdown"])
        blob = json.dumps(stale)
        for marker in SECRET_MARKERS:
            self.assertNotIn(marker, blob)

    def test_stale_legacy_cache_rebuilds_meters_without_adding_breakdown(self) -> None:
        payload = {
            "provider": "codex",
            "displayName": "Codex",
            "plan": "ChatGPT Plus",
            "remainingPercent": 94,
            "secondaryRemainingPercent": 80,
            "resetAt": "2026-08-17T12:00:00+02:00",
            "status": "ok",
        }
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = tmp
            try:
                write_success("codex", payload)
                stale = stale_payload("codex", "Codex", "Current refresh failed")
            finally:
                if old is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old
        self.assertIsNotNone(stale)
        assert stale is not None
        self.assertNotIn("breakdown", stale)
        self.assertEqual(stale["remainingPercent"], 94)
        self.assertEqual(stale["secondaryRemainingPercent"], 80)
        self.assertEqual(stale["meters"][0]["label"], "Usage limit")
        self.assertEqual(stale["meters"][0]["resetAt"], "2026-08-17T12:00:00+02:00")
        self.assertEqual(stale["meters"][1]["remainingPercent"], 80)
        self.assertNotIn("resetAt", stale["meters"][1])

    def test_cache_refuses_secret_fields(self) -> None:
        payload = project_ok(
            provider="codex",
            display_name="Codex",
            plan="ChatGPT Plus",
            meters=[{"label": "Weekly limit", "remainingPercent": 90}],
        )
        payload["access_token"] = "sk-ant-test-secret"
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = tmp
            try:
                with self.assertRaises(ValueError):
                    write_success("codex", payload)
            finally:
                if old is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old

    def test_cache_refuses_nested_and_mixed_case_secret_keys(self) -> None:
        base = project_ok(
            provider="stepfun",
            display_name="StepFun",
            plan="Step Plan",
            meters=[{"label": "Credits", "remainingPercent": 80}],
        )
        cases = [
            {"meters": [{"label": "Credits", "remainingPercent": 80, "Access_Token": "x"}]},
            {"breakdown": [{"label": "Credits", "remainingPercent": 80, "cookie": "x"}]},
            {"Authorization": "x"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = tmp
            try:
                for extra in cases:
                    bad = dict(base)
                    bad.update(extra)
                    with self.assertRaises(ValueError):
                        write_success("stepfun", bad)

                path = write_success("stepfun", base)
                envelope = json.loads(path.read_text())
                self.assertEqual(set(envelope.keys()), {"fetchedAt", "provider", "data"})
                self.assertEqual(
                    set(envelope["data"].keys()),
                    {
                        "provider",
                        "displayName",
                        "plan",
                        "remainingPercent",
                        "resetAt",
                        "status",
                        "breakdown",
                        "meters",
                    },
                )
            finally:
                if old is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old


class ProviderEdgeCaseTests(unittest.TestCase):
    def test_numeric_parsers_reject_bool_inf_and_nan(self) -> None:
        bad_values = [True, False, float("inf"), float("-inf"), float("nan")]
        for bad in bad_values:
            self.assertIsNone(claude_utilization({"utilization": bad}))
            self.assertIsNone(claude_remaining_from_used(bad))
            self.assertFalse(claude_expired(bad))
            self.assertIsNone(codex_meter_from_window({"used_percent": bad}))
            self.assertIsNone(CursorProvider._remaining_from_used_percent(bad))

    def test_codex_unreadable_auth_file_is_auth_unavailable(self) -> None:
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            auth_file = Path(tmp) / "auth.json"
            auth_file.write_text('{"tokens": {"access_token": "x"}}')
            provider = CodexProvider(auth_path=auth_file)
            with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                with self.assertRaises(ProviderError) as ctx:
                    provider._load_auth()
            self.assertEqual(ctx.exception.code, "auth_unavailable")

    def test_codex_refresh_non_json_is_upstream_error(self) -> None:
        from unittest import mock

        class NonJsonResp:
            def read(self) -> bytes:
                return b"<html>bad gateway</html>"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        provider = CodexProvider(auth_path=Path("/nonexistent/auth.json"))
        with mock.patch("urllib.request.urlopen", return_value=NonJsonResp()):
            with self.assertRaises(ProviderError) as ctx:
                provider._refresh_tokens({"tokens": {"refresh_token": "ref"}})
        self.assertEqual(ctx.exception.code, "upstream_error")


if __name__ == "__main__":
    unittest.main()
