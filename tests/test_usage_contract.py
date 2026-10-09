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
from providers import error_payload  # noqa: E402
from providers.claude import ClaudeProvider  # noqa: E402
from providers.codex import CodexProvider  # noqa: E402
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
            os.environ["XDG_CACHE_HOME"] = tmp
            try:
                with self.assertRaises(ValueError):
                    write_success("codex", payload)
            finally:
                os.environ.pop("XDG_CACHE_HOME", None)


if __name__ == "__main__":
    unittest.main()
