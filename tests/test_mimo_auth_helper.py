"""Unit tests for Xiaomi MiMo auth helper (T5 & T7)."""

from __future__ import annotations

import io
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

COLLECTOR = Path(__file__).resolve().parents[1] / "collector"
if str(COLLECTOR) not in sys.path:
    sys.path.insert(0, str(COLLECTOR))

import mimo_auth_helper  # noqa: E402
from providers import ProviderError  # noqa: E402
from secret_store import SecretStoreError  # noqa: E402

FIXTURE_KEY = "tp-fake-fixture-key-0001"


class MiMoAuthHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._saved = {k: os.environ.pop(k, None) for k in ("XIAOMI_API_KEY", "MIMO_API_KEY")}
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_empty_clipboard(self) -> None:
        buf = io.StringIO()
        with (
            mock.patch.object(mimo_auth_helper, "read_clipboard", return_value=""),
            mock.patch.object(mimo_auth_helper, "secret_set") as mock_set,
            redirect_stdout(buf),
        ):
            rc = mimo_auth_helper.main(["mimo_auth_helper.py", "clipboard", "sgp"])
        self.assertEqual(rc, 1)
        self.assertEqual(buf.getvalue().strip(), "empty")
        mock_set.assert_not_called()

    def test_invalid_prefix_stores_nothing(self) -> None:
        buf = io.StringIO()
        with (
            mock.patch.object(mimo_auth_helper, "read_clipboard", return_value="sk-not-a-tp-key"),
            mock.patch.object(mimo_auth_helper, "secret_set") as mock_set,
            redirect_stdout(buf),
        ):
            rc = mimo_auth_helper.main(["mimo_auth_helper.py", "clipboard", "sgp"])
        self.assertEqual(rc, 1)
        self.assertEqual(buf.getvalue().strip(), "invalid")
        mock_set.assert_not_called()

    def test_clipboard_working_clears_clipboard(self) -> None:
        buf = io.StringIO()
        with (
            mock.patch.object(mimo_auth_helper, "read_clipboard", return_value=FIXTURE_KEY),
            mock.patch.object(mimo_auth_helper, "secret_set") as mock_set,
            mock.patch.object(mimo_auth_helper, "clear_clipboard") as mock_clear,
            mock.patch("providers.mimo.MiMoProvider.fetch_usage", return_value={"status": "ok"}),
            redirect_stdout(buf),
        ):
            rc = mimo_auth_helper.main(["mimo_auth_helper.py", "clipboard", "cn"])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "working")
        self.assertNotIn(FIXTURE_KEY, buf.getvalue())
        self.assertNotIn(FIXTURE_KEY[:12], buf.getvalue())
        mock_set.assert_called_once_with("mimo", "token-plan-key", FIXTURE_KEY)
        mock_clear.assert_called_once()

    def test_401_gives_auth_failed_and_network_gives_unavailable(self) -> None:
        for exc, expected in [
            (ProviderError("auth_unavailable", "rejected"), "auth_failed"),
            (ProviderError("upstream_error", "HTTP 500"), "unavailable"),
            (urllib.error.URLError("offline"), "unavailable"),
        ]:
            buf = io.StringIO()
            with (
                mock.patch.object(mimo_auth_helper, "secret_get", return_value=FIXTURE_KEY),
                mock.patch("providers.mimo.MiMoProvider.fetch_usage", side_effect=exc),
                redirect_stdout(buf),
            ):
                rc = mimo_auth_helper.main(["mimo_auth_helper.py", "status", "ams"])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), expected)
            self.assertNotIn(FIXTURE_KEY[:12], buf.getvalue())

    def test_status_missing_store_error_and_clear(self) -> None:
        # missing
        buf = io.StringIO()
        with mock.patch.object(mimo_auth_helper, "secret_get", return_value=None), redirect_stdout(buf):
            rc = mimo_auth_helper.main(["mimo_auth_helper.py", "status", "sgp"])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "missing")

        # store_error
        buf = io.StringIO()
        with (
            mock.patch.object(mimo_auth_helper, "secret_get", side_effect=SecretStoreError("locked")),
            redirect_stdout(buf),
        ):
            rc = mimo_auth_helper.main(["mimo_auth_helper.py", "status", "sgp"])
        self.assertEqual(rc, 1)
        self.assertEqual(buf.getvalue().strip(), "store_error")

        # clear -> cleared
        buf = io.StringIO()
        with mock.patch.object(mimo_auth_helper, "secret_delete") as mock_del, redirect_stdout(buf):
            rc = mimo_auth_helper.main(["mimo_auth_helper.py", "clear", "sgp"])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "cleared")
        mock_del.assert_called_once_with("mimo", "token-plan-key")

    def test_invalid_region_returns_2(self) -> None:
        rc = mimo_auth_helper.main(["mimo_auth_helper.py", "status", "us"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
