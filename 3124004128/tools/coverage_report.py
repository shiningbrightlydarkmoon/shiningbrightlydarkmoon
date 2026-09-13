"""用自定义行追踪器统计语句覆盖率。

不依赖 coverage / pytest-cov，方便在没有网络的评测环境里也能复现。
统计口径：能被 AST 识别为"语句"的行中，有多少行在测试运行时被执行过。

用法::

    python tools/coverage_report.py
"""

import ast
import contextlib
import os
import sys
import unittest
from typing import Dict, List, Set

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGET_FILES = [
    "main.py",
    "src/config.py",
    "src/exceptions.py",
    "src/text_utils.py",
    "src/file_io.py",
    "src/similarity.py",
]


def collect_statement_lines(path: str) -> Set[int]:
    """用 AST 找出一个 Python 文件里所有语句所在的行号。"""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    return {node.lineno for node in ast.walk(tree) if isinstance(node, ast.stmt)}


class LineCoverage:
    """极简行覆盖率追踪器：只记录目标文件里被执行过的行号。

    之所以不用标准库的 ``trace``，是因为它在"只有 docstring 和类定义"的
    模块上会漏记行号，导致覆盖率虚低。
    """

    def __init__(self, target_files: List[str]) -> None:
        self.targets = {os.path.abspath(path) for path in target_files}
        self.executed: Dict[str, Set[int]] = {}

    def _trace(self, frame, event, arg):
        filename = os.path.abspath(frame.f_code.co_filename)
        if filename not in self.targets:
            return None
        if event == "line":
            self.executed.setdefault(filename, set()).add(frame.f_lineno)
        return self._trace

    def __enter__(self) -> "LineCoverage":
        sys.settrace(self._trace)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        sys.settrace(None)


def run_tests_under_coverage() -> Dict[str, Set[int]]:
    """在追踪器下运行全部单元测试，返回 {文件绝对路径: 执行过的行号}。"""
    sys.path.insert(0, PROJECT_ROOT)
    target_paths = [os.path.join(PROJECT_ROOT, name) for name in TARGET_FILES]
    with LineCoverage(target_paths) as coverage:
        # 测试模块的 import 也放在追踪范围内，这样被测模块的模块级语句
        # （类定义、常量赋值等）同样会被统计到，否则覆盖率会虚低。
        suite = unittest.TestLoader().discover(
            os.path.join(PROJECT_ROOT, "tests"), top_level_dir=PROJECT_ROOT
        )
        with open(os.devnull, "w") as devnull, contextlib.redirect_stderr(devnull):
            runner = unittest.TextTestRunner(stream=devnull, verbosity=0)
            runner.run(suite)
    return coverage.executed


def main() -> None:
    executed = run_tests_under_coverage()
    rows = []
    total_statements = 0
    total_hit = 0
    for relative in TARGET_FILES:
        path = os.path.join(PROJECT_ROOT, relative)
        statements = collect_statement_lines(path)
        hits = executed.get(os.path.abspath(path), set()) & statements
        total = len(statements)
        hit = len(hits)
        total_statements += total
        total_hit += hit
        rate = (hit / total * 100) if total else 100.0
        rows.append((relative, total, hit, rate))

    lines = ["文件                      语句数   已覆盖    覆盖率", "-" * 52]
    for relative, total, hit, rate in rows:
        lines.append(f"{relative:<22}{total:>8}{hit:>8}{rate:>9.1f}%")
    lines.append("-" * 52)
    overall = (total_hit / total_statements * 100) if total_statements else 100.0
    lines.append(f"{'合计':<22}{total_statements:>8}{total_hit:>8}{overall:>9.1f}%")

    report = "\n".join(lines)
    print(report)
    output_path = os.path.join(PROJECT_ROOT, "docs", "coverage_stdlib.txt")
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(report + "\n")
    print(f"\n报告已写入：{output_path}")


if __name__ == "__main__":
    main()
