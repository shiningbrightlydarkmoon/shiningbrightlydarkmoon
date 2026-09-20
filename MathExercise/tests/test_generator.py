import unittest

from src.expression import Expression
from src.generator import GenerationError, ProblemGenerator
from src.parser import parse_expression


def leaves(expression: Expression) -> list:
    if expression.is_leaf:
        return [expression]
    return leaves(expression.left) + leaves(expression.right)


class GeneratorTests(unittest.TestCase):
    def test_generate_unique_valid_problems(self) -> None:
        expressions = ProblemGenerator(10, seed=7).generate(1000)
        keys = {expression.canonical_key() for expression in expressions}
        self.assertEqual(len(expressions), 1000)
        self.assertEqual(len(keys), 1000)
        for expression in expressions:
            self.assertLessEqual(expression.operator_count, 3)
            expression.evaluate()
            for leaf in leaves(expression):
                self.assertGreaterEqual(leaf.value.numerator, 0)
                self.assertLess(leaf.value.value, 10)
                self.assertLess(leaf.value.denominator, 10)

    def test_rendered_problem_can_be_parsed_back(self) -> None:
        expressions = ProblemGenerator(20, seed=12).generate(100)
        for expression in expressions:
            reparsed = parse_expression(expression.render())
            self.assertEqual(expression.canonical_key(), reparsed.canonical_key())

    def test_small_domain_reports_insufficient_space(self) -> None:
        with self.assertRaises(GenerationError):
            ProblemGenerator(1, seed=1).generate(10_000)


if __name__ == "__main__":
    unittest.main()
