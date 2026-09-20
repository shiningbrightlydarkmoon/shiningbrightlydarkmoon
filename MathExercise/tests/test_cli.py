import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.exercise_io import read_exercises


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN = PROJECT_ROOT / "main.py"


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MAIN), *arguments],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_generate_and_grade_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = self.run_cli("-n", "12", "-r", "10", cwd=root)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            exercises = read_exercises(root / "Exercises.txt")
            self.assertEqual(len(exercises), 12)

            answers = root / "Answers.txt"
            answers.write_text(
                "\n".join(
                    f"{item.number}. {item.expression.evaluate().format()}"
                    for item in exercises
                )
                + "\n",
                encoding="utf-8",
            )
            graded = self.run_cli("-e", "Exercises.txt", "-a", "Answers.txt", cwd=root)
            self.assertEqual(graded.returncode, 0, graded.stderr)
            self.assertEqual(
                (root / "Grade.txt").read_text(encoding="utf-8"),
                "Correct: 12 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)\nWrong: 0 ()\n",
            )

    def test_missing_r_prints_help(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("-n", "5", cwd=Path(directory))
            self.assertEqual(result.returncode, 2)
            self.assertIn("-r", result.stderr)
            self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
