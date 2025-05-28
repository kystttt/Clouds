import unittest
import os
from unittest.mock import patch, MagicMock, call, mock_open
from source.googledrive.GoogleAction import GoogleAction


class TestGoogleAction(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "source.googledrive.GoogleAction.oauth_to_drive", return_value=MagicMock()
        )
        self.mock_auth = patcher.start()
        self.addCleanup(patcher.stop)
        self.action = GoogleAction()
        self.mock_files = MagicMock()
        self.action.service.files = MagicMock(return_value=self.mock_files)

    @patch("source.googledrive.GoogleAction.os.walk")
    @patch("source.googledrive.GoogleAction.Bar")
    def test_upload_nested_folders(self, MockBar, mock_os_walk):
        root_path = os.path.join(os.sep, "path")
        subdir_path = os.path.join(root_path, "subdir")
        mock_os_walk.return_value = [
            (root_path, ["subdir"], ["file1.txt"]),
            (subdir_path, [], ["file2.txt"]),
        ]
        mock_bar = MagicMock()
        MockBar.return_value = mock_bar
        action = GoogleAction()
        action._get_or_create_folder = MagicMock(
            side_effect=lambda name, pid: f"{name}_id"
        )
        action._upload_file = MagicMock()
        action.upload(root_path)
        expected_folder_calls = [
            call("path", None),
            call("subdir", "path_id"),
        ]
        action._get_or_create_folder.assert_has_calls(
            expected_folder_calls, any_order=False
        )
        expected_upload_calls = [
            call(os.path.join(root_path, "file1.txt"), "path_id"),
            call(os.path.join(subdir_path, "file2.txt"), "subdir_id"),
        ]
        action._upload_file.assert_has_calls(expected_upload_calls, any_order=True)

        self.assertEqual(action._upload_file.call_count, 2)
        self.assertEqual(mock_bar.next.call_count, 2)
        mock_bar.finish.assert_called_once()

    @patch("source.googledrive.GoogleAction.os.walk")
    @patch("source.googledrive.GoogleAction.Bar")
    def test_upload_single_folder_multiple_files(self, MockBar, mock_os_walk):
        root_path = os.path.join(os.sep, "rootfolder")
        mock_os_walk.return_value = [
            (root_path, [], ["fileA.txt", "fileB.txt", "fileC.txt"]),
        ]
        mock_bar = MagicMock()
        MockBar.return_value = mock_bar
        action = GoogleAction()
        action._get_or_create_folder = MagicMock(return_value="rootfolder_id")
        action._upload_file = MagicMock()
        action.upload(root_path)
        action._get_or_create_folder.assert_called_once_with("rootfolder", None)

        expected_upload_calls = [
            call(os.path.join(root_path, "fileA.txt"), "rootfolder_id"),
            call(os.path.join(root_path, "fileB.txt"), "rootfolder_id"),
            call(os.path.join(root_path, "fileC.txt"), "rootfolder_id"),
        ]
        action._upload_file.assert_has_calls(expected_upload_calls, any_order=True)

        self.assertEqual(action._upload_file.call_count, 3)
        self.assertEqual(mock_bar.next.call_count, 3)
        mock_bar.finish.assert_called_once()

    def test_get_or_create_folder_exists_without_parent(self):
        folder_id = "existing-folder-id"
        self.mock_files.list.return_value.execute.return_value = {
            "files": [{"id": folder_id}]
        }
        result = self.action._get_or_create_folder("MyFolder", None)
        self.assertEqual(result, folder_id)
        self.mock_files.create.assert_not_called()
        expected_query = "name='MyFolder' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        self.mock_files.list.assert_called_with(
            q=expected_query, spaces="drive", fields="files(id)"
        )

    def test_get_or_create_folder_exists_with_parent(self):
        folder_id = "existing-folder-id"
        parent_id = "parent123"
        self.mock_files.list.return_value.execute.return_value = {
            "files": [{"id": folder_id}]
        }
        result = self.action._get_or_create_folder("MyFolder", parent_id)
        self.assertEqual(result, folder_id)
        self.mock_files.create.assert_not_called()
        expected_query = f"name='MyFolder' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_id}' in parents"
        self.mock_files.list.assert_called_with(
            q=expected_query, spaces="drive", fields="files(id)"
        )

    def test_get_or_create_folder_not_exists_creates(self):
        self.mock_files.list.return_value.execute.return_value = {"files": []}
        new_folder_id = "new-folder-id"
        self.mock_files.create.return_value.execute.return_value = {"id": new_folder_id}
        parent_id = "parent123"
        result = self.action._get_or_create_folder("NewFolder", parent_id)
        self.assertEqual(result, new_folder_id)
        expected_body = {
            "name": "NewFolder",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        self.mock_files.create.assert_called_with(body=expected_body, fields="id")
        self.mock_files.create.return_value.execute.assert_called_once()

    def test_get_or_create_folder_not_exists_creates_no_parent(self):
        self.mock_files.list.return_value.execute.return_value = {"files": []}
        new_folder_id = "new-folder-id-2"
        self.mock_files.create.return_value.execute.return_value = {"id": new_folder_id}
        result = self.action._get_or_create_folder("NewFolderNoParent", None)
        self.assertEqual(result, new_folder_id)
        expected_body = {
            "name": "NewFolderNoParent",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [],
        }
        self.mock_files.create.assert_called_with(body=expected_body, fields="id")
        self.mock_files.create.return_value.execute.assert_called_once()

    @patch("source.googledrive.GoogleAction.Bar")
    @patch("time.sleep", return_value=None)
    @patch("sys.exit")
    def test_delete_backup_on_cloud_success(self, mock_exit, mock_sleep, MockBar):
        self.action._get_folder_id_by_name = MagicMock(side_effect=["folder123", None])
        files = [{"id": "file1"}, {"id": "file2"}]
        self.action._list_all_files_recursive = MagicMock(return_value=files)
        mock_bar = MagicMock()
        MockBar.return_value = mock_bar
        delete_mock = MagicMock()
        self.action.service.files().delete = MagicMock(return_value=delete_mock)
        delete_mock.execute = MagicMock()
        self.action.delete_backup_on_cloud("backup_name")
        self.action._get_folder_id_by_name.assert_any_call("backup_name")
        self.action._list_all_files_recursive.assert_called_once_with("folder123")
        expected_calls = [
            call(fileId="file1"),
            call(fileId="file2"),
            call(fileId="folder123"),
        ]
        actual_calls = self.action.service.files().delete.call_args_list
        self.assertEqual(actual_calls, expected_calls)
        self.assertEqual(delete_mock.execute.call_count, 3)
        MockBar.assert_called_once_with("Deleting", fill="█", max=2)
        self.assertEqual(mock_bar.next.call_count, 2)
        mock_bar.finish.assert_called_once()
        self.assertEqual(mock_sleep.call_count, 3)
        mock_exit.assert_called_once_with(0)

    @patch("source.googledrive.GoogleAction.Bar")
    @patch("time.sleep", return_value=None)
    @patch("sys.exit")
    def test_delete_backup_on_cloud_backup_not_deleted(
        self, mock_exit, mock_sleep, MockBar
    ):
        self.action._get_folder_id_by_name = MagicMock(
            side_effect=["folder123", "folder123"]
        )
        files = [{"id": "file1"}]
        self.action._list_all_files_recursive = MagicMock(return_value=files)
        mock_bar = MagicMock()
        MockBar.return_value = mock_bar
        delete_mock = MagicMock()
        self.action.service.files().delete = MagicMock(return_value=delete_mock)
        delete_mock.execute = MagicMock()
        with patch("builtins.print") as mock_print:
            self.action.delete_backup_on_cloud("backup_name")
        mock_print.assert_any_call("Error: backup wasn't deleted")
        mock_exit.assert_called_once_with(1)

    @patch("builtins.print")
    def test_list_of_files_on_backup_not_found(self, mock_print):
        self.action._get_folder_id_by_name = MagicMock(return_value=None)
        self.action.list_of_files_on_backup("missing_backup")
        mock_print.assert_called_once_with(
            "Error: Backup folder 'missing_backup' not found."
        )

    @patch("builtins.print")
    def test_list_of_files_on_backup_empty_folder(self, mock_print):
        self.action._get_folder_id_by_name = MagicMock(return_value="folder123")
        self.action.service.files().list().execute = MagicMock(
            return_value={"files": []}
        )
        self.action.list_of_files_on_backup("backup_name")
        mock_print.assert_any_call("backup_name: ")
        self.assertEqual(mock_print.call_count, 1)

    @patch("builtins.print")
    def test_list_of_files_on_backup_unusual_mimetype(self, mock_print):
        self.action._get_folder_id_by_name = MagicMock(return_value="folder123")

        self.action.service.files().list().execute = MagicMock(
            return_value={
                "files": [
                    {
                        "id": "file123",
                        "name": "UnknownFile.type",
                        "mimeType": "application/x-custom",
                    }
                ]
            }
        )
        self.action.list_of_files_on_backup("custom_backup")
        mock_print.assert_any_call("custom_backup: ")
        mock_print.assert_any_call(" UnknownFile.type:")

    @patch("builtins.print")
    def test_list_of_files_on_backup_multiple_root_items(self, mock_print):
        self.action._get_folder_id_by_name = MagicMock(return_value="root_id")

        def list_side_effect(**kwargs):
            q = kwargs.get("q", "")
            if "'root_id' in parents" in q:
                return {
                    "files": [
                        {
                            "id": "folderA",
                            "name": "FolderA",
                            "mimeType": "application/vnd.google-apps.folder",
                        },
                        {"id": "fileX", "name": "FileX.txt", "mimeType": "text/plain"},
                    ]
                }
            elif "'folderA' in parents" in q:
                return {"files": []}
            return {"files": []}

        mock_files = MagicMock()
        mock_list = MagicMock(
            side_effect=lambda **kwargs: MagicMock(
                execute=MagicMock(return_value=list_side_effect(**kwargs))
            )
        )
        mock_files.list = mock_list
        self.action.service.files = MagicMock(return_value=mock_files)

        self.action.list_of_files_on_backup("BackupX")

        printed = [call.args[0] for call in mock_print.call_args_list]
        self.assertIn("BackupX: ", printed)
        self.assertIn(" FolderA:", printed)
        self.assertIn(" FileX.txt:", printed)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("os.utime")
    @patch("os.path.getmtime")
    @patch("source.googledrive.GoogleAction.MediaIoBaseDownload")
    @patch("source.googledrive.GoogleAction.datetime")
    @patch("source.googledrive.GoogleAction.Bar")
    @patch("sys.exit")
    def test_download_simple_structure(
        self,
        mock_exit,
        mock_bar_class,
        mock_datetime,
        mock_downloader_class,
        mock_getmtime,
        mock_utime,
        mock_exists,
        mock_makedirs,
        mock_open_file,
    ):
        mock_datetime.fromisoformat.return_value.timestamp.return_value = 1000000
        mock_datetime.fromtimestamp.return_value = (
            mock_datetime.fromisoformat.return_value
        )
        mock_datetime.fromisoformat.return_value.replace.return_value = (
            mock_datetime.fromisoformat.return_value
        )
        mock_bar = MagicMock()
        mock_bar_class.return_value = mock_bar
        mock_downloader = MagicMock()
        mock_downloader.next_chunk.side_effect = [(None, False), (None, True)]
        mock_downloader_class.return_value = mock_downloader

        self.action.service.files().list().execute.side_effect = [
            {"files": [{"id": "backup_folder_id"}]},
            {
                "files": [
                    {
                        "id": "file1",
                        "name": "test.txt",
                        "mimeType": "text/plain",
                        "modifiedTime": "2024-01-01T00:00:00Z",
                    }
                ]
            },
            {
                "files": [
                    {
                        "id": "file1",
                        "name": "test.txt",
                        "mimeType": "text/plain",
                        "modifiedTime": "2024-01-01T00:00:00Z",
                    }
                ]
            },
        ]
        mock_exists.return_value = False
        local_root = os.path.join("/tmp/downloads", "backup_name")
        expected_file_path = os.path.join(local_root, "test.txt")
        self.action.download("backup_name", "/tmp/downloads")
        mock_bar_class.assert_called_once_with("Downloading", fill="█", max=1)
        mock_makedirs.assert_called_once_with(local_root, exist_ok=True)
        mock_open_file.assert_called_once_with(expected_file_path, "wb")
        mock_exit.assert_called_once_with(0)
        self.assertEqual(mock_bar.next.call_count, 1)


if __name__ == "__main__":
    unittest.main()
