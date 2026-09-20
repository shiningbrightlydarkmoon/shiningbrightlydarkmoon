from __future__ import annotations

import random
from collections import OrderedDict


from .expression import Expression, ExpressionError
from .rational import Rational


class GenerationError(RuntimeError):
    """Raised when the requested number of unique problems cannot be made."""


class ProblemGenerator:
    """Generate valid, unique arithmetic expressions with at most 3 operators."""

    _OPERATORS = ("+", "-", "×", "÷")

    def __init__(self, r: int, seed: int | None = None) -> None:
        if r < 1:
            raise GenerationError("参数 -r 必须是正整数")
        self.r = r
        self.random = random.Random(seed)

    def generate(self, count: int) -> list[Expression]:
        if count < 1:
            raise GenerationError("参数 -n 必须是正整数")

        if self.r <= 3:
            return self._generate_small_domain(count)

        seen: set[str] = set()
        results: list[Expression] = []
        max_attempts = max(50_000, count * 120)
        attempts = 0

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            operator_count = self.random.randint(1, 3)
            candidate = self._build_random_expression(operator_count)
            if candidate is None:
                continue
            key = candidate.canonical_key()
            if key in seen:
                continue
            try:
                candidate.evaluate()
            except ExpressionError:
                continue
            seen.add(key)
            results.append(candidate)

        if len(results) < count:
            raise GenerationError(
                f"无法生成 {count} 道互不重复的合法题目（r={self.r}）。"
                "请增大 -r 或减少 -n。"
            )
        return results

    def _build_random_expression(self, operator_count: int) -> Expression | None:
        if operator_count == 0:
            return Expression.leaf(self._random_leaf())

        left_operator_count = self.random.randrange(operator_count)
        right_operator_count = operator_count - 1 - left_operator_count
        left = self._build_random_expression(left_operator_count)
        right = self._build_random_expression(right_operator_count)
        if left is None or right is None:
            return None
        return Expression.binary(self.random.choice(self._OPERATORS), left, right)

    def _random_leaf(self) -> Rational:
        # Fractions and mixed numbers are deliberately common. All generated
        # leaves have a value and denominator strictly smaller than r.
        if self.r == 1:
            return Rational.from_parts(0)

        category = self.random.random()
        if category < 0.35:
            return Rational.from_parts(self.random.randrange(self.r))

        if category < 0.7 and self.r > 2:
            denominator = self.random.randrange(2, self.r)
            numerator = self.random.randrange(1, denominator)
            return Rational.from_parts(numerator, denominator)

        if self.r > 2:
            denominator = self.random.randrange(2, self.r)
            numerator = self.random.randrange(1, denominator)
            max_whole = self.r - 1
            while True:
                whole = self.random.randint(1, max_whole)
                if whole + numerator / denominator < self.r:
                    return Rational.from_parts(whole * denominator + numerator, denominator)

        return Rational.from_parts(self.random.randrange(self.r))

    def _all_small_leaves(self) -> list[Rational]:
        values: OrderedDict[tuple[int, int], Rational] = OrderedDict()
        for natural in range(self.r):
            value = Rational.from_parts(natural)
            values[(value.numerator, value.denominator)] = value
        if self.r > 2:
            for denominator in range(2, self.r):
                for numerator in range(1, denominator):
                    value = Rational.from_parts(numerator, denominator)
                    values[(value.numerator, value.denominator)] = value
                    for whole in range(1, self.r):
                        mixed = Rational.from_parts(whole * denominator + numerator, denominator)
                        if mixed.value < self.r:
                            values[(mixed.numerator, mixed.denominator)] = mixed
        return list(values.values())

    def _generate_small_domain(self, count: int) -> list[Expression]:
        """Enumerate the complete search space for very small -r values.

        This avoids spending time on random retries when the domain is too
        small to satisfy a request such as -r 1 -n 10000.
        """

        leaves = self._all_small_leaves()
        levels: list[list[Expression]] = [[Expression.leaf(value) for value in leaves]]
        found: OrderedDict[str, Expression] = OrderedDict()

        for operator_count in range(1, 4):
            level: OrderedDict[str, Expression] = OrderedDict()
            for left_count in range(operator_count):
                right_count = operator_count - 1 - left_count
                for left in levels[left_count]:
                    for right in levels[right_count]:
                        for operator in self._OPERATORS:
                            candidate = Expression.binary(operator, left, right)
                            try:
                                candidate.evaluate()
                            except ExpressionError:
                                continue
                            key = candidate.canonical_key()
                            if key not in level:
                                level[key] = candidate
                                if key not in found:
                                    found[key] = candidate
                                    if len(found) >= count:
                                        return list(found.values())[:count]
            levels.append(list(level.values()))

        raise GenerationError(
            f"无法生成 {count} 道互不重复的合法题目（r={self.r}）。"
            "请增大 -r 或减少 -n。"
        )
