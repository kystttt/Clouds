import unittest
from unittest.mock import patch, MagicMock
import source.main


class TestMain(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "source.googledrive.google_auth.oauth_to_drive",
            return_value=MagicMock()
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    @patch("source.main.sys.argv", ["main.py", "g_download",
                                    "remote", "local"])
    @patch("source.main.GoogleAction")
    def test_g_download(self, MockGoogle):
        source.main.main()
        MockGoogle.return_value.download.assert_called_once_with(
            "remote", "local")

    @patch("source.main.sys.argv", ["main.py", "g_upload", "file"])
    @patch("source.main.GoogleAction")
    def test_g_upload(self, MockGoogle):
        source.main.main()
        MockGoogle.return_value.backup.assert_called_once_with("file")

    @patch("source.main.sys.exit")
    @patch("source.main.sys.argv", ["main.py", "g_download", "only_remote"])
    def test_g_download_arg_missing(self, mock_exit):
        mock_exit.side_effect = SystemExit(1)
        with self.assertRaises(SystemExit) as cm:
            source.main.main()
        self.assertEqual(cm.exception.code, 1)
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
