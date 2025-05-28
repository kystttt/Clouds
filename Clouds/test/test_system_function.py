import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
            with open(os.path.join(self.sub_dir, f"file_sub{i}.txt"), "w") as f:
                f.write("test")


    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)


    @patch("source.system_function.Bar")
    @patch("source.system_function.time.sleep", return_value=None)
    def test_delete_success(self, mock_sleep, mock_bar):
        mock_bar.return_value = MagicMock(spec=["next", "finish"])
        system = SystemFunction(interactive=False)
        result = system.delete_backup_on_pc(self.test_dir)
        self.assertFalse(os.path.exists(self.test_dir))
        self.assertIsNone(result)


    @patch("source.system_function.Bar")
    def test_not_a_directory_error(self, mock_bar):
        system = SystemFunction(interactive=False)
        with tempfile.NamedTemporaryFile() as temp_file:
            result = system.delete_backup_on_pc(temp_file.name)
            self.assertIsNone(result)


    @patch("source.system_function.os.remove", side_effect=PermissionError("Нет прав"))
    @patch("source.system_function.time.sleep", return_value=None)
    @patch("source.system_function.Bar")
    def test_permission_error(self, mock_bar, mock_sleep, mock_remove):
        mock_bar.return_value = MagicMock(spec=["next", "finish"])
        system = SystemFunction(interactive=False)
        result = system.delete_backup_on_pc(self.test_dir)
        self.assertIsNone(result)


    @patch("source.system_function.os.remove", side_effect=OSError("Ошибка ОС"))
    @patch("source.system_function.time.sleep", return_value=None)
    @patch("source.system_function.Bar")
    def test_os_error(self, mock_bar, mock_sleep, mock_remove):
        mock_bar.return_value = MagicMock(spec=["next", "finish"])
        system = SystemFunction(interactive=False)
        result = system.delete_backup_on_pc(self.test_dir)
        self.assertIsNone(result)




if __name__ == '__main__':
    unittest.main()
