from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exercise_io import ExerciseFileError, write_exercises
from .generator import GenerationError, ProblemGenerator
from .grader import grade


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Myapp.exe",
        description="生成小学四则运算题，或批改题目和答案文件。",
    )
    parser.add_argument("-n", type=int, default=None, help="生成题目的数量")
    parser.add_argument("-r", type=int, default=None, help="数值和分数分母的范围（不包含 r）")
    parser.add_argument("-e", metavar="exercisefile", help="待判分的题目文件")
    parser.add_argument("-a", metavar="answerfile", help="待判分的答案文件")
    return parser


def _print_help_error(parser: argparse.ArgumentParser, message: str) -> int:
    print(f"错误: {message}", file=sys.stderr)
    parser.print_help(sys.stderr)
    return 2

def _configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)

    has_grading_args = args.e is not None or args.a is not None
    has_generation_args = args.n is not None or args.r is not None

    if has_grading_args and has_generation_args:
        return _print_help_error(parser, "不能在同一个命令中同时使用生成参数和判分参数")

    if has_grading_args:
        if args.e is None or args.a is None:
            return _print_help_error(parser, "判分时必须同时提供 -e 和 -a")
        try:
            result = grade(args.e, args.a)
        except ExerciseFileError as exc:
            return _print_help_error(parser, str(exc))
        output = Path.cwd() / "Grade.txt"
        print(f"判分完成，结果已写入: {output}")
        print(result.format(), end="")
        return 0

    if args.r is None:
        return _print_help_error(parser, "生成题目时必须提供 -r 参数")
    if args.r < 1:
        return _print_help_error(parser, "参数 -r 必须是正整数")
    count = 10 if args.n is None else args.n
    if count < 1:
        return _print_help_error(parser, "参数 -n 必须是正整数")

    try:
        generator = ProblemGenerator(args.r)
        expressions = generator.generate(count)
    except GenerationError as exc:
        return _print_help_error(parser, str(exc))

    output = Path.cwd() / "Exercises.txt"
    try:
        write_exercises(output, expressions)
    except OSError as exc:
        return _print_help_error(parser, f"无法写入题目文件: {exc}")
    print(f"已生成 {len(expressions)} 道题目: {output}")
    return 0
