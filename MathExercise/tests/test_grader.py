import tempfile
import unittest
from pathlib import Path

from src.grader import grade
from src.parser import parse_expression


class GraderTests(unittest.TestCase):
    def test_grade_numbered_answers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exercise_path = root / "Exercises.txt"
            answer_path = root / "Answers.txt"
            grade_path = root / "Grade.txt"
            exercise_path.write_text(
                "1. 1/6 + 1/8 =\n"
                "2. 2 + 3 =\n"
                "3. 1 ÷ 2 =\n",
                encoding="utf-8",
            )
            answer_path.write_text(
                "1. 7/24\n"
                "2. 4\n"
                "3. 1/2\n",
                encoding="utf-8",
            )
            result = grade(exercise_path, answer_path, grade_path)
            self.assertEqual(result.correct, (1, 3))
            self.assertEqual(result.wrong, (2,))
            self.assertEqual(
                grade_path.read_text(encoding="utf-8"),
                "Correct: 2 (1, 3)\nWrong: 1 (2)\n",
            )

    def test_grade_bare_answers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exercise_path = root / "Exercises.txt"
            answer_path = root / "Answers.txt"
            exercise_path.write_text("1. 1 ÷ 2 =\n", encoding="utf-8")
            answer_path.write_text("1/2\n", encoding="utf-8")
            result = grade(exercise_path, answer_path, root / "Grade.txt")
            self.assertEqual(result.correct, (1,))
            self.assertEqual(result.wrong, ())

    def test_expression_parser_can_read_generated_style(self) -> None:
        expression = parse_expression("3/4 + 2’3/8")
        self.assertEqual(expression.evaluate().format(), "3’1/8")


if __name__ == "__main__":
    unittest.main()
