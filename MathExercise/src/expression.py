from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .rational import Rational


class ExpressionError(ValueError):
    """Raised when an expression is structurally or semantically invalid."""


_PRECEDENCE = {"+": 1, "-": 1, "×": 2, "÷": 2}


@dataclass(frozen=True)
class Expression:
    """A binary expression tree.

    Leaf nodes only have ``value`` set. Operator nodes have ``operator``,
    ``left`` and ``right`` set.
    """

    operator: Optional[str] = None
    value: Optional[Rational] = None
    left: Optional["Expression"] = None
    right: Optional["Expression"] = None

    @classmethod
    def leaf(cls, value: Rational) -> "Expression":
        return cls(value=value)

    @classmethod
    def binary(cls, operator: str, left: "Expression", right: "Expression") -> "Expression":
        if operator not in _PRECEDENCE:
            raise ExpressionError(f"不支持的运算符: {operator}")
        return cls(operator=operator, left=left, right=right)

    @property
    def is_leaf(self) -> bool:
        return self.operator is None

    @property
    def operator_count(self) -> int:
        if self.is_leaf:
            return 0
        return 1 + self.left.operator_count + self.right.operator_count

    def evaluate(self) -> Rational:
        """Evaluate and enforce the assignment's intermediate-result rules."""

        if self.is_leaf:
            if self.value is None:
                raise ExpressionError("数字节点缺少数值")
            return self.value

        if self.left is None or self.right is None:
            raise ExpressionError("运算节点缺少子表达式")

        left = self.left.evaluate()
        right = self.right.evaluate()

        if self.operator == "+":
            return left + right
        if self.operator == "-":
            if left < right:
                raise ExpressionError("减法产生了负数")
            return left - right
        if self.operator == "×":
            return left * right
        if self.operator == "÷":
            if right.is_zero():
                raise ExpressionError("除数不能为 0")
            result = left / right
            if not result.is_proper():
                raise ExpressionError("除法结果必须为正的真分数")
            return result
        raise ExpressionError(f"不支持的运算符: {self.operator}")

    def canonical_key(self) -> str:
        """Return a key invariant under +/× child swaps, but not flattening.

        For example, ``2+3`` and ``3+2`` have one key. ``(1+2)+3``
        and ``3+(2+1)`` have one key, while ``(1+2)+3`` and
        ``(3+2)+1`` keep different keys.
        """

        if self.is_leaf:
            if self.value is None:
                raise ExpressionError("数字节点缺少数值")
            return f"N{self.value.numerator}/{self.value.denominator}"

        if self.left is None or self.right is None:
            raise ExpressionError("运算节点缺少子表达式")

        left_key = self.left.canonical_key()
        right_key = self.right.canonical_key()
        if self.operator in {"+", "×"}:
            left_key, right_key = sorted((left_key, right_key))
        return f"({self.operator}{left_key},{right_key})"

    def render(self) -> str:
        return self._render()

    def _render(self) -> str:
        if self.is_leaf:
            if self.value is None:
                raise ExpressionError("数字节点缺少数值")
            return self.value.format()

        if self.left is None or self.right is None or self.operator is None:
            raise ExpressionError("运算节点缺少子表达式")

        left = self._render_child(self.left, is_right=False)
        right = self._render_child(self.right, is_right=True)
        return f"{left} {self.operator} {right}"

    def _render_child(self, child: "Expression", is_right: bool) -> str:
        if self.operator is None:
            return child._render()
        if child.is_leaf:
            return child._render()

        child_precedence = _PRECEDENCE[child.operator]
        parent_precedence = _PRECEDENCE[self.operator]
        needs_parentheses = child_precedence < parent_precedence
        if child_precedence == parent_precedence and is_right:
            # Preserve the exact tree. This matters because the assignment
            # distinguishes a+(b+c) from (a+b)+c.
            needs_parentheses = True
        rendered = child._render()
        return f"({rendered})" if needs_parentheses else rendered
