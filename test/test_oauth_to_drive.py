import unittest
from unittest.mock import patch, mock_open, MagicMock
from source.googledrive.google_auth import oauth_to_drive


class TestOAuthToDrive(unittest.TestCase):

    @patch("source.googledrive.google_auth.build")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
    @patch("google.auth.transport.requests.Request")
    def test_valid_token(
        self, mock_request, mock_from_file, mock_exists, mock_open_file,
            mock_build
    ):
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        mock_build.return_value = "DRIVE_SERVICE"

        result = oauth_to_drive()

        mock_build.assert_called_once_with("drive", "v3",
                                           credentials=mock_creds)
        self.assertEqual(result, "DRIVE_SERVICE")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("google.oauth2.credentials.Credentials."
           "from_authorized_user_file")
    @patch("google.auth.transport.requests.Request")
    @patch("google_auth_oauthlib.flow.InstalledAppFlow."
           "from_client_secrets_file")
    @patch("source.googledrive.google_auth.build")
    def test_expired_token_with_refresh(
        self,
        mock_build,
        mock_flow,
        mock_request,
        mock_from_file,
        mock_exists,
        mock_open_file,
    ):
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = True
        mock_from_file.return_value = mock_creds

        result = oauth_to_drive()

        mock_creds.refresh.assert_called_once()
        mock_build.assert_called_once_with("drive", "v3",
                                           credentials=mock_creds)
        self.assertEqual(result, mock_build.return_value)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
    @patch("google_auth_oauthlib.flow.InstalledAppFlow."
           "from_client_secrets_file")
    @patch("source.googledrive.google_auth.build")
    def test_new_token_created(
        self,
        mock_build,
        mock_flow_from_file,
        mock_from_file,
        mock_exists,
        mock_open_file,
    ):
        mock_exists.return_value = False
        mock_creds = MagicMock()
        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_from_file.return_value = mock_flow

        result = oauth_to_drive()

        mock_open_file.assert_called_once_with("..token.json", "w")
        mock_creds.to_json.assert_called_once()
        mock_build.assert_called_once_with("drive", "v3",
                                           credentials=mock_creds)
        self.assertEqual(result, mock_build.return_value)

    @patch(
        "google.oauth2.credentials.Credentials.from_authorized_user_file",
        side_effect=Exception("bad"),
    )
    def test_oauth_exception(self, mock_from_file):
        with patch("sys.exit") as mock_exit:
            oauth_to_drive()
            mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
