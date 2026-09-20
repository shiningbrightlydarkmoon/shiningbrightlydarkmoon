from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .expression import Expression
from .parser import ParseError, parse_expression


_EXERCISE_RE = re.compile(r"^\s*(\d+)\.\s*(.*?)\s*=\s*$")
_ANSWER_NUMBER_RE = re.compile(r"^\s*(\d+)\.\s*(.*?)\s*$")


@dataclass(frozen=True)
class ExerciseItem:
    number: int
    expression: Expression


class ExerciseFileError(ValueError):
    """Raised when an exercise or answer file has an invalid format."""


def write_exercises(path: str | Path, expressions: Iterable[Expression]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for number, expression in enumerate(expressions, start=1):
            handle.write(f"{number}. {expression.render()} =\n")
    return output


def read_exercises(path: str | Path) -> list[ExerciseItem]:
    source = Path(path)
    if not source.exists():
        raise ExerciseFileError(f"题目文件不存在: {source}")

    items: list[ExerciseItem] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            match = _EXERCISE_RE.fullmatch(line)
            if not match:
                raise ExerciseFileError(f"题目文件第 {line_number} 行格式错误: {line}")
            number = int(match.group(1))
            try:
                expression = parse_expression(match.group(2))
            except ParseError as exc:
                raise ExerciseFileError(
                    f"题目文件第 {line_number} 行表达式错误: {exc}"
                ) from exc
            items.append(ExerciseItem(number, expression))
    if not items:
        raise ExerciseFileError("题目文件为空")
    return items


def read_answer_lines(path: str | Path) -> list[str]:
    source = Path(path)
    if not source.exists():
        raise ExerciseFileError(f"答案文件不存在: {source}")
    with source.open("r", encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    if not lines:
        raise ExerciseFileError("答案文件为空")
    return lines


def parse_answer_lines(lines: list[str]) -> list[tuple[int | None, str]]:
    """Return (number, answer) pairs.

    Both numbered answers and bare answers are accepted. The caller can
    decide whether to match by number or by position.
    """

    parsed: list[tuple[int | None, str]] = []
    for line in lines:
        match = _ANSWER_NUMBER_RE.fullmatch(line)
        if match:
            parsed.append((int(match.group(1)), match.group(2).strip()))
        else:
            parsed.append((None, line))
    return parsed
