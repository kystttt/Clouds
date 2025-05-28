import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
import unittest
from source.constants import Y_URL, headers
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta
from io import BytesIO
from unittest.mock import patch, MagicMock, mock_open
import gzip
import tempfile
from source.yandexdrive.YandexAction import YandexAction


class TestYandexAction(unittest.TestCase):
    def setUp(self):
        self.yandex_action = YandexAction(Y_URL, headers)
        self.backup_name = 'testFolder_2025_04_11'


    def fake_file_stat(mod_time):
        stat_result = MagicMock()
        stat_result.st_mtime = mod_time
        return stat_result

    @patch("requests.get")
    @patch("requests.put")
    def test_create_folder_when_not_exist(self, mock_put, mock_get):
        mock_get.return_value.status_code = 404
        self.yandex_action.create_folder("test_folder")
        mock_put.assert_called_once_with(f'{Y_URL}?path=test_folder', headers=self.yandex_action.headers)


    @patch("requests.get")
    @patch("requests.put")
    def test_create_folder_when_created(self, mock_put, mock_get):
        mock_get.return_value.status_code = 200
        self.yandex_action.create_folder("test_folder")
        mock_put.assert_not_called()


    @patch('source.yandexdrive.YandexAction.requests.get')
    def test_backup_not_found(self, mock_get):
        mock_get.return_value.status_code = 404
        with self.assertRaises(SystemExit) as cm:
            self.yandex_action.delete_backup_on_cloud(self.backup_name)
        self.assertEqual(cm.exception.code, 1)


    @patch('source.yandexdrive.YandexAction.requests.get')
    @patch('source.yandexdrive.YandexAction.requests.delete')
    @patch.object(YandexAction, '_count_files')
    @patch('source.yandexdrive.YandexAction.Bar')
    def test_backup_deleted_successfully(self, mock_bar, mock_count_files, mock_delete, mock_get):
        mock_get.side_effect = [
            MagicMock(status_code=200),
            MagicMock(status_code=404)
        ]
        mock_count_files.return_value = 2
        bar_instance = MagicMock()
        mock_bar.return_value = bar_instance
        with self.assertRaises(SystemExit) as cm:
            self.yandex_action.delete_backup_on_cloud(self.backup_name)
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_get.call_count, 2)
        mock_delete.assert_called_once()
        mock_count_files.assert_called_once_with(self.backup_name)
        self.assertEqual(bar_instance.next.call_count, 2)
        bar_instance.finish.assert_called_once()


    @patch('source.yandexdrive.YandexAction.requests.get')
    @patch('source.yandexdrive.YandexAction.requests.delete')
    @patch.object(YandexAction, '_count_files')
    @patch('source.yandexdrive.YandexAction.Bar')
    def test_backup_delete_failed(self, mock_bar, mock_count_files, mock_delete, mock_get):
        mock_get.side_effect = [
            MagicMock(status_code=200),
            MagicMock(status_code=200)
        ]
        mock_count_files.return_value = 1
        bar_instance = MagicMock()
        mock_bar.return_value = bar_instance
        with patch('builtins.print') as mock_print:
            self.yandex_action.delete_backup_on_cloud(self.backup_name)
            mock_print.assert_any_call("Error: backup doesn't deleted", 200)
            self.assertEqual(bar_instance.next.call_count, 1)
            bar_instance.finish.assert_called_once()


    @patch("source.yandexdrive.YandexAction.os.utime")
    @patch("source.yandexdrive.YandexAction.os.stat")
    def test_compress_file(self, mock_stat, mock_utime):
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_path = f.name
            f.write(b"test data")
        try:
            expected_gz_name = f"{test_path}.gz"
            buffer, compressed_name = self.yandex_action.compress(test_path)
            self.assertEqual(
                os.path.basename(compressed_name),
                os.path.basename(expected_gz_name)
            )
            self.assertIsInstance(buffer, BytesIO)
            buffer.seek(0)
            with gzip.GzipFile(fileobj=buffer, mode='rb') as gz:
                content = gz.read()
            self.assertEqual(content, b"test data")
            mock_utime.assert_called_once_with(
                os.path.basename(expected_gz_name),
                (1234567890, 1234567890)
            )

        finally:
            import os as real_os
            if real_os.path.exists(test_path):
                real_os.remove(test_path)
            if real_os.path.exists(compressed_name):
                real_os.remove(compressed_name)


    @patch("source.yandexdrive.YandexAction.requests.get")
    @patch("source.yandexdrive.YandexAction.requests.put")
    @patch("source.yandexdrive.YandexAction.os.stat")
    @patch("source.yandexdrive.YandexAction.YandexAction.compress")
    def test_upload_file_does_not_exist_on_cloud(self, compress_mock, stat_mock, put_mock, get_mock):
        os.environ["UNIT_TEST_MODE"] = "1"
        with TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, "test.txt")
            with open(file_path, "w") as f:
                f.write("hello")
            get_mock.side_effect = [
                MagicMock(status_code=404),
                MagicMock(json=lambda: {'href': 'https://upload-url'})
            ]
            buffer = BytesIO(b"compressed")
            compress_mock.return_value = (buffer, "test.txt.gz")
            fake_stat = MagicMock()
            fake_stat.st_mtime = datetime.now(timezone.utc).timestamp()
            stat_mock.return_value = fake_stat
            self.yandex_action.upload(file_path, "backup-folder")
            compress_mock.assert_called_once()
            put_mock.assert_called_once_with("https://upload-url", data=buffer.getvalue())

    @patch("source.yandexdrive.YandexAction.os.path.exists")
    @patch("source.yandexdrive.YandexAction.os.stat")
    @patch("source.yandexdrive.YandexAction.requests.get")
    def test_file_up_to_date_no_download(self, requests_get_mock, stat_mock, exists_mock):
        os.environ["UNIT_TEST_MODE"] = "1"
        with TemporaryDirectory() as tmpdir:
            backup_name = "testFolder_2025_04_11"
            exists_mock.side_effect = lambda path: True
            cloud_time = datetime(2025, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
            pc_time = cloud_time + timedelta(seconds=-1)
            stat_mock.return_value.st_mtime = pc_time.timestamp()
            requests_get_mock.side_effect = [
                MagicMock(status_code=200, json=lambda: {
                    '_embedded': {
                        'items': [{
                            'path': f'disk:/{backup_name}/file.txt.gz',
                            'type': 'file'
                        }]
                    }
                }),
                MagicMock(status_code=200, json=lambda: {'modified': '2025-05-01T10:00:00'}),
            ]

            with self.assertRaises(SystemExit) as cm:
                self.yandex_action.download(backup_name, tmpdir)
            self.assertEqual(cm.exception.code, 0)

    @patch("source.yandexdrive.YandexAction.requests.get")
    def test_backup_not_found_raises_exit(self, requests_get_mock):
        os.environ["UNIT_TEST_MODE"] = "1"
        with TemporaryDirectory() as tmpdir:
            requests_get_mock.return_value.status_code = 404

            with self.assertRaises(SystemExit) as cm:
                self.yandex_action.download("nonexistent", tmpdir)
            self.assertEqual(cm.exception.code, 1)

    @patch("source.yandexdrive.YandexAction.sys.exit")
    @patch("source.yandexdrive.YandexAction.os.makedirs")
    @patch("source.yandexdrive.YandexAction.os.path.exists")
    @patch("source.yandexdrive.YandexAction.os.utime")
    @patch("source.yandexdrive.YandexAction.shutil.copyfileobj")
    @patch("source.yandexdrive.YandexAction.gzip.open")
    @patch("source.yandexdrive.YandexAction.open", new_callable=mock_open)
    @patch("source.yandexdrive.YandexAction.requests.get")
    @patch("source.yandexdrive.YandexAction.os.stat")
    def test_download_new_file(
            self, stat_mock, requests_get_mock, open_mock, gzip_open_mock,
            copyfileobj_mock, utime_mock, exists_mock, makedirs_mock, sys_exit_mock
    ):
        os.environ["UNIT_TEST_MODE"] = "1"
        with TemporaryDirectory() as tmpdir:
            sys_exit_mock.side_effect = lambda code: print(f"[MOCKED] sys.exit({code})")

            backup_name = "testFolder_2025_04_11"
            full_local_path = os.path.join(tmpdir, backup_name)
            exists_mock.side_effect = lambda path: False
            stat_mock.return_value.st_mtime = datetime(2025, 4, 1, 12, 0, 0).timestamp()
            requests_get_mock.side_effect = [
                MagicMock(status_code=200, json=lambda: {
                    '_embedded': {
                        'items': [{
                            'path': f'disk:/{backup_name}/test.txt.gz',
                            'type': 'file'
                        }]
                    }
                }),
                MagicMock(status_code=200, json=lambda: {'modified': '2025-05-01T10:00:00'}),
                MagicMock(status_code=200, json=lambda: {'href': 'https://fake-download-url'}),
                MagicMock(
                    status_code=200,
                    iter_content=lambda chunk_size: [b'compressed'],
                    __enter__=lambda s: s,
                    __exit__=lambda *args: None
                )
            ]
            gzip_open_context = MagicMock()
            gzip_open_context.__enter__.return_value = BytesIO(b'hello world')
            gzip_open_mock.return_value = gzip_open_context
            open_file_mock = mock_open()
            open_mock.side_effect = open_file_mock
            self.yandex_action.download(backup_name, tmpdir)
            sys_exit_mock.assert_called_once_with(0)
            makedirs_mock.assert_any_call(full_local_path, exist_ok=False)
            open_mock.assert_called()
            gzip_open_mock.assert_called()
            copyfileobj_mock.assert_called()

    @patch("source.yandexdrive.YandexAction.requests.get")
    def test_list_of_files_on_backup_flat_structure(self, mock_get):
        """
        Тестирует вывод списка файлов в корневом каталоге без вложенных директорий.
        """
        mock_get.return_value.json.return_value = {
            '_embedded': {
                'items': [
                    {'name': 'file1.txt', 'type': 'file', 'path': 'testFolder/file1.txt'},
                    {'name': 'file2.txt', 'type': 'file', 'path': 'testFolder/file2.txt'}
                ]
            }
        }

        with patch("builtins.print") as mock_print:
            self.yandex_action.list_of_files_on_backup("testFolder")

        mock_print.assert_any_call("testFolder: ")
        mock_print.assert_any_call(" file1.txt")
        mock_print.assert_any_call(" file2.txt")
        self.assertEqual(mock_get.call_count, 1)

    @patch("source.yandexdrive.YandexAction.requests.get")
    def test_list_of_files_on_backup_flat_structure(self, mock_get):

        mock_get.return_value.json.return_value = {
            '_embedded': {
                'items': [
                    {'name': 'file1.txt', 'type': 'file', 'path': 'testFolder/file1.txt'},
                    {'name': 'file2.txt', 'type': 'file', 'path': 'testFolder/file2.txt'}
                ]
            }
        }

        with patch("builtins.print") as mock_print:
            self.yandex_action.list_of_files_on_backup("testFolder")

        mock_print.assert_any_call("testFolder: ")
        mock_print.assert_any_call(" file1.txt")
        mock_print.assert_any_call(" file2.txt")
        self.assertEqual(mock_get.call_count, 1)

    @patch("source.yandexdrive.YandexAction.requests.get")
    def test_list_of_files_on_backup_empty_folder(self, mock_get):
        """
        Тестирует поведение при пустой директории.
        """
        mock_get.return_value.json.return_value = {
            '_embedded': {
                'items': []
            }
        }

        with patch("builtins.print") as mock_print:
            self.yandex_action.list_of_files_on_backup("emptyFolder")

        mock_print.assert_any_call("emptyFolder: ")
        self.assertEqual(mock_get.call_count, 1)

    @patch("source.yandexdrive.YandexAction.requests.get")
    def test_list_of_files_on_backup_missing_embedded(self, mock_get):
        mock_get.return_value.json.return_value = {
            'unexpected': 'structure'
        }
        with patch("builtins.print") as mock_print:
            self.yandex_action.list_of_files_on_backup("corruptedFolder")
        mock_print.assert_any_call("corruptedFolder: ")
        self.assertEqual(mock_print.call_count, 1)
        self.assertEqual(mock_get.call_count, 1)


if __name__ == '__main__':
    unittest.main()
