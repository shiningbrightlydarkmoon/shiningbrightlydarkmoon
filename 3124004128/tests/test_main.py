"""``main`` 入口模块的单元测试。"""

import os
import tempfile
import unittest
from unittest import mock

from main import main, parse_args, run
from src.exceptions import InvalidArgumentError


class ParseArgsTest(unittest.TestCase):
    """测试命令行参数解析。"""

    def test_valid_arguments(self):
        self.assertEqual(
            parse_args(["main.py", "orig.txt", "copy.txt", "ans.txt"]),
            ("orig.txt", "copy.txt", "ans.txt"),
        )

    def test_too_few_arguments_raises(self):
        with self.assertRaises(InvalidArgumentError):
            parse_args(["main.py", "orig.txt"])

    def test_too_many_arguments_raises(self):
        with self.assertRaises(InvalidArgumentError):
            parse_args(["main.py", "a", "b", "c", "d"])


class RunTest(unittest.TestCase):
    """测试程序整体运行与退出码。"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _write(self, name, content):
        path = os.path.join(self.temp_dir.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def test_wrong_argument_count_returns_2(self):
        self.assertEqual(run(["main.py"]), 2)

    def test_missing_input_file_returns_1(self):
        original = self._write("orig.txt", "今天天气晴")
        answer = os.path.join(self.temp_dir.name, "ans.txt")
        missing = os.path.join(self.temp_dir.name, "missing.txt")
        self.assertEqual(run(["main.py", original, missing, answer]), 1)

    def test_successful_run_writes_answer(self):
        original = self._write("orig.txt", "今天是星期天，天气晴。")
        copy = self._write("copy.txt", "今天是星期天，天气晴。")
        answer = os.path.join(self.temp_dir.name, "ans.txt")
        self.assertEqual(run(["main.py", original, copy, answer]), 0)
        with open(answer, encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), "1.00")

    def test_both_files_empty_returns_1(self):
        original = self._write("empty_orig.txt", "")
        copy = self._write("empty_copy.txt", "")
        answer = os.path.join(self.temp_dir.name, "ans.txt")
        self.assertEqual(run(["main.py", original, copy, answer]), 1)


class MainEntryTest(unittest.TestCase):
    """测试脚本入口的退出码传递。"""

    def test_main_exits_with_run_code(self):
        argv_patch = mock.patch("sys.argv", ["main.py"])
        with argv_patch, self.assertRaises(SystemExit) as context:
            main()
        self.assertEqual(context.exception.code, 2)
