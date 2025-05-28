import unittest
import os
import tempfile
from source.SystemFunction import SystemFunction
from unittest.mock import patch, MagicMock


class TestSystemFunction(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.test_dir, "sub")
        os.mkdir(self.sub_dir)
        for i in range(3):
            with open(os.path.join(self.test_dir, f"file{i}.txt"), "w") as f:
                f.write("test")
            with open(os.path.join(self.sub_dir, f"file_sub{i}.txt"),
                      "w") as f:
                f.write("test")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)

    @patch("source.SystemFunction.Bar")
    @patch("source.SystemFunction.time.sleep", return_value=None)
    def test_delete_success(self, mock_sleep, mock_bar):
        mock_bar.return_value = MagicMock(spec=["next", "finish"])
        system = SystemFunction(interactive=False)
        result = system.delete_backup_on_pc(self.test_dir)
        self.assertFalse(os.path.exists(self.test_dir))
        self.assertIsNone(result)

    @patch("source.SystemFunction.Bar")
    @patch("source.SystemFunction.time.sleep", return_value=None)
    def test_delete_empty_directory(self, mock_sleep, mock_bar):
        empty_dir = tempfile.mkdtemp()
        mock_bar.return_value = MagicMock(spec=["next", "finish"])
        system = SystemFunction(interactive=False)

        result = system.delete_backup_on_pc(empty_dir)
        self.assertFalse(os.path.exists(empty_dir))
        self.assertIsNone(result)

    @patch(
        "source.SystemFunction.os.rmdir", side_effect=OSError("Ошибка удаления"
                                                              " папки")
    )
    @patch("source.SystemFunction.time.sleep", return_value=None)
    @patch("source.SystemFunction.Bar")
    def test_rmdir_oserror(self, mock_bar, mock_sleep, mock_rmdir):
        mock_bar.return_value = MagicMock(spec=["next", "finish"])
        system = SystemFunction(interactive=False)

        result = system.delete_backup_on_pc(self.test_dir)
        self.assertIsNone(result)
        self.assertTrue(mock_rmdir.called)

    @patch(
        "source.SystemFunction.os.remove", side_effect=PermissionError(
            "Нет доступа")
    )
    @patch("source.SystemFunction.Bar")
    @patch("source.SystemFunction.time.sleep", return_value=None)
    def test_raise_in_unit_test_mode(self, mock_sleep, mock_bar, mock_remove):
        os.environ["UNIT_TEST_MODE"] = "1"
        system = SystemFunction(interactive=False)
        mock_bar.return_value = MagicMock(spec=["next", "finish"])

        with self.assertRaises(PermissionError):
            system.delete_backup_on_pc(self.test_dir)

        os.environ.pop("UNIT_TEST_MODE")

    @patch("source.SystemFunction.time.sleep", return_value=None)
    @patch("source.SystemFunction.Bar")
    def test_progress_bar_correct_calls(self, mock_bar, mock_sleep):
        mock_bar_instance = MagicMock(spec=["next", "finish"])
        mock_bar.return_value = mock_bar_instance
        system = SystemFunction(interactive=False)
        system.delete_backup_on_pc(self.test_dir)
        self.assertEqual(mock_bar_instance.next.call_count, 6)
        mock_bar_instance.finish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
