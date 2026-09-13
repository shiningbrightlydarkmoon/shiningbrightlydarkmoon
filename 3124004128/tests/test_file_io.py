"""``file_io`` 模块的单元测试。"""

import os
import tempfile
import unittest
from unittest import mock

from src.exceptions import FileReadError, OutputWriteError
from src.file_io import read_text, write_answer


class ReadTextTest(unittest.TestCase):
    """测试多编码文本读取。"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _write(self, name, content, encoding):
        path = os.path.join(self.temp_dir.name, name)
        with open(path, "w", encoding=encoding) as handle:
            handle.write(content)
        return path

    def test_read_utf8(self):
        path = self._write("utf8.txt", "中文内容", "utf-8")
        self.assertEqual(read_text(path), "中文内容")

    def test_read_utf8_with_bom(self):
        path = self._write("bom.txt", "中文内容", "utf-8-sig")
        self.assertEqual(read_text(path), "中文内容")

    def test_read_gbk(self):
        path = self._write("gbk.txt", "中文内容", "gbk")
        self.assertEqual(read_text(path), "中文内容")

    def test_missing_file_raises(self):
        with self.assertRaises(FileReadError):
            read_text(os.path.join(self.temp_dir.name, "not_here.txt"))

    def test_empty_path_raises(self):
        with self.assertRaises(FileReadError):
            read_text("")

    def test_directory_raises(self):
        with self.assertRaises(FileReadError):
            read_text(self.temp_dir.name)

    def test_os_error_raises_file_read_error(self):
        path = self._write("broken.txt", "abc", "utf-8")
        open_patch = mock.patch("builtins.open", side_effect=OSError("boom"))
        with open_patch, self.assertRaises(FileReadError):
            read_text(path)


class WriteAnswerTest(unittest.TestCase):
    """测试答案写入。"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def test_write_then_read_back(self):
        path = os.path.join(self.temp_dir.name, "answer.txt")
        write_answer(path, "0.86")
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), "0.86")

    def test_missing_directory_raises(self):
        path = os.path.join(self.temp_dir.name, "no_such_dir", "answer.txt")
        with self.assertRaises(OutputWriteError):
            write_answer(path, "0.86")

    def test_empty_path_raises(self):
        with self.assertRaises(OutputWriteError):
            write_answer("", "0.86")

    def test_os_error_raises_output_write_error(self):
        path = os.path.join(self.temp_dir.name, "answer.txt")
        open_patch = mock.patch("builtins.open", side_effect=OSError("boom"))
        with open_patch, self.assertRaises(OutputWriteError):
            write_answer(path, "0.86")
