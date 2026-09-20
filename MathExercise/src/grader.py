from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exercise_io import (
    ExerciseFileError,
    parse_answer_lines,
    read_answer_lines,
    read_exercises,
)
from .expression import ExpressionError
from .rational import Rational, RationalError


@dataclass(frozen=True)
class GradeResult:
    correct: tuple[int, ...]
    wrong: tuple[int, ...]

    def format(self) -> str:
        correct_numbers = ", ".join(str(number) for number in self.correct)
        wrong_numbers = ", ".join(str(number) for number in self.wrong)
        return (
            f"Correct: {len(self.correct)} ({correct_numbers})\n"
            f"Wrong: {len(self.wrong)} ({wrong_numbers})\n"
        )


def grade(exercise_path: str | Path, answer_path: str | Path, output_path: str | Path | None = None) -> GradeResult:
    exercises = read_exercises(exercise_path)
    answer_lines = parse_answer_lines(read_answer_lines(answer_path))

    has_numbers = [number is not None for number, _ in answer_lines]
    if any(has_numbers) and not all(has_numbers):
        raise ExerciseFileError("答案文件不能混用带编号和不带编号的格式")

    if all(has_numbers):
        answer_map = {number: answer for number, answer in answer_lines if number is not None}
        answers = [answer_map.get(item.number, "") for item in exercises]
    else:
        answers = [answer for _, answer in answer_lines]

    correct: list[int] = []
    wrong: list[int] = []
    for index, item in enumerate(exercises):
        raw_answer = answers[index] if index < len(answers) else ""
        try:
            expected = item.expression.evaluate()
            actual = Rational.parse(raw_answer)
            is_correct = actual == expected
        except (ExpressionError, RationalError, ZeroDivisionError):
            is_correct = False
        if is_correct:
            correct.append(item.number)
        else:
            wrong.append(item.number)

    result = GradeResult(tuple(correct), tuple(wrong))
    destination = Path(output_path) if output_path is not None else Path.cwd() / "Grade.txt"
    destination.write_text(result.format(), encoding="utf-8")
    return result
