"""Unit tests for StepFun auth helper and CLI auth status mapping (W-04)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

COLLECTOR = Path(__file__).resolve().parents[1] / "collector"
if str(COLLECTOR) not in sys.path:
    sys.path.insert(0, str(COLLECTOR))

import stepfun_auth_helper  # noqa: E402
from providers import ProviderError  # noqa: E402


def _load_ai_usage_module():
    loader = importlib.machinery.SourceFileLoader("ai_usage_cli", str(COLLECTOR / "ai-usage"))
    spec = importlib.util.spec_from_loader("ai_usage_cli", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


FAKE_TOKEN = "a" * 45 + "." + "b" * 45


class StepFunAuthHelperTests(unittest.TestCase):
    def test_verify_token_working(self) -> None:
        with mock.patch("providers.stepfun.StepFunProvider.fetch_usage", return_value={"status": "ok"}):
            self.assertEqual(stepfun_auth_helper.verify_token(), "working")

    def test_verify_token_auth_unavailable_is_auth_failed(self) -> None:
        with mock.patch(
            "providers.stepfun.StepFunProvider.fetch_usage",
            side_effect=ProviderError("auth_unavailable", "rejected"),
        ):
            self.assertEqual(stepfun_auth_helper.verify_token(), "auth_failed")

    def test_verify_token_upstream_error_is_unavailable(self) -> None:
        with mock.patch(
            "providers.stepfun.StepFunProvider.fetch_usage",
            side_effect=ProviderError("upstream_error", "HTTP 503"),
        ):
            self.assertEqual(stepfun_auth_helper.verify_token(), "unavailable")

    def test_verify_token_generic_exception_is_unavailable(self) -> None:
        with mock.patch(
            "providers.stepfun.StepFunProvider.fetch_usage",
            side_effect=urllib.error.URLError("offline"),
        ):
            self.assertEqual(stepfun_auth_helper.verify_token(), "unavailable")

    def test_cmd_clipboard_clears_clipboard_on_unavailable(self) -> None:
        buf = io.StringIO()
        with (
            mock.patch.object(stepfun_auth_helper, "read_clipboard", return_value=FAKE_TOKEN),
            mock.patch.object(stepfun_auth_helper, "secret_set") as mock_set,
            mock.patch.object(stepfun_auth_helper, "clear_clipboard") as mock_clear,
            mock.patch(
                "providers.stepfun.StepFunProvider.fetch_usage",
                side_effect=ProviderError("upstream_error", "network down"),
            ),
            redirect_stdout(buf),
        ):
            rc = stepfun_auth_helper.cmd_clipboard()
        self.assertEqual(rc, 1)
        self.assertEqual(buf.getvalue().strip(), "unavailable")
        self.assertNotIn(FAKE_TOKEN, buf.getvalue())
        mock_set.assert_called_once_with("stepfun", "oasis-token", FAKE_TOKEN)
        mock_clear.assert_called_once()

    def test_cmd_status_returns_zero_for_unavailable_and_auth_failed(self) -> None:
        for side_effect, expected in [
            (ProviderError("auth_unavailable", "rejected"), "auth_failed"),
            (ProviderError("upstream_error", "offline"), "unavailable"),
            (urllib.error.URLError("dns"), "unavailable"),
            ({"status": "ok"}, "working"),
        ]:
            buf = io.StringIO()
            with (
                mock.patch.object(stepfun_auth_helper, "secret_get", return_value=FAKE_TOKEN),
                mock.patch("providers.stepfun.StepFunProvider.fetch_usage", side_effect=side_effect)
                if isinstance(side_effect, Exception)
                else mock.patch("providers.stepfun.StepFunProvider.fetch_usage", return_value=side_effect),
                redirect_stdout(buf),
            ):
                rc = stepfun_auth_helper.cmd_status()
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), expected)
            self.assertNotIn(FAKE_TOKEN, buf.getvalue())

    def test_cli_auth_stepfun_set_and_status_mapping(self) -> None:
        cli = _load_ai_usage_module()
        for side_effect, expected_status, expected_set_rc in [
            ({"status": "ok"}, "working", 0),
            (ProviderError("auth_unavailable", "rejected"), "auth_failed", 1),
            (ProviderError("upstream_error", "timeout"), "unavailable", 1),
            (urllib.error.URLError("offline"), "unavailable", 1),
        ]:
            # status
            buf = io.StringIO()
            fetch_patch = (
                mock.patch.object(cli.StepFunProvider, "fetch_usage", side_effect=side_effect)
                if isinstance(side_effect, Exception)
                else mock.patch.object(cli.StepFunProvider, "fetch_usage", return_value=side_effect)
            )
            with (
                mock.patch.object(cli, "secret_configured", return_value=True),
                fetch_patch,
                redirect_stdout(buf),
            ):
                rc = cli.main(["auth", "stepfun", "status"])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), expected_status)
            self.assertNotIn(FAKE_TOKEN, buf.getvalue())

            # set
            buf = io.StringIO()
            fake_stdin = io.StringIO(FAKE_TOKEN + "\n")
            fetch_patch = (
                mock.patch.object(cli.StepFunProvider, "fetch_usage", side_effect=side_effect)
                if isinstance(side_effect, Exception)
                else mock.patch.object(cli.StepFunProvider, "fetch_usage", return_value=side_effect)
            )
            with (
                mock.patch.object(sys, "stdin", fake_stdin),
                mock.patch.object(cli, "secret_set") as mock_set,
                fetch_patch,
                redirect_stdout(buf),
            ):
                rc = cli.main(["auth", "stepfun", "set"])
            self.assertEqual(rc, expected_set_rc)
            self.assertEqual(buf.getvalue().strip(), expected_status)
            self.assertNotIn(FAKE_TOKEN, buf.getvalue())
            mock_set.assert_called_once_with("stepfun", "oasis-token", FAKE_TOKEN)


if __name__ == "__main__":
    unittest.main()
