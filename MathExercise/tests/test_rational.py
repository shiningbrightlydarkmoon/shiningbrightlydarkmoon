import unittest

from src.rational import Rational, RationalError


class RationalTests(unittest.TestCase):
    def test_parse_fraction_and_mixed_number(self) -> None:
        self.assertEqual(Rational.parse("3/5").format(), "3/5")
        self.assertEqual(Rational.parse("2’3/8"), Rational.from_parts(19, 8))
        self.assertEqual(Rational.parse("2'3/8").format(), "2’3/8")

    def test_fraction_arithmetic(self) -> None:
        result = Rational.parse("1/6") + Rational.parse("1/8")
        self.assertEqual(result.format(), "7/24")

    def test_format_integer(self) -> None:
        self.assertEqual(Rational.from_parts(8, 2).format(), "4")

    def test_reject_zero_denominator(self) -> None:
        with self.assertRaises(RationalError):
            Rational.parse("1/0")


if __name__ == "__main__":
    unittest.main()
