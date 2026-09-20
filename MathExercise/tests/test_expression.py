import unittest

from src.expression import ExpressionError
from src.parser import parse_expression


class ExpressionTests(unittest.TestCase):
    def test_commutative_duplicates(self) -> None:
        self.assertEqual(
            parse_expression("2 + 3").canonical_key(),
            parse_expression("3 + 2").canonical_key(),
        )
        self.assertEqual(
            parse_expression("2 × 3").canonical_key(),
            parse_expression("3 × 2").canonical_key(),
        )

    def test_nested_duplicate_rule(self) -> None:
        self.assertEqual(
            parse_expression("1 + 2 + 3").canonical_key(),
            parse_expression("3 + (2 + 1)").canonical_key(),
        )
        self.assertNotEqual(
            parse_expression("1 + 2 + 3").canonical_key(),
            parse_expression("3 + 2 + 1").canonical_key(),
        )

    def test_render_round_trip_preserves_tree(self) -> None:
        for text in ("1 + 2 + 3", "3 + (2 + 1)", "1 + (2 + 3)", "(8 ÷ 9) + 1"):
            original = parse_expression(text)
            rendered = parse_expression(original.render())
            self.assertEqual(original.canonical_key(), rendered.canonical_key())

    def test_subtraction_rejects_negative_intermediate_result(self) -> None:
        with self.assertRaises(ExpressionError):
            parse_expression("1 - 2").evaluate()

    def test_division_must_be_proper_fraction(self) -> None:
        self.assertEqual(parse_expression("1 ÷ 2").evaluate().format(), "1/2")
        with self.assertRaises(ExpressionError):
            parse_expression("2 ÷ 1").evaluate()
        with self.assertRaises(ExpressionError):
            parse_expression("0 ÷ 1").evaluate()


if __name__ == "__main__":
    unittest.main()
