from __future__ import annotations

from .expression import Expression, ExpressionError
from .rational import Rational, RationalError


class ParseError(ValueError):
    """Raised when an exercise expression cannot be parsed."""


class ExpressionParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.position = 0

    def parse(self) -> Expression:
        expression = self._parse_expression()
        self._skip_spaces()
        if self.position != len(self.text):
            raise ParseError(f"表达式后存在无法识别的内容: {self.text[self.position:]}")
        return expression

    def _parse_expression(self) -> Expression:
        left = self._parse_term()
        while True:
            operator = self._peek_operator({"+", "-"})
            if operator is None:
                return left
            self._read_operator()
            right = self._parse_term()
            left = Expression.binary(operator, left, right)

    def _parse_term(self) -> Expression:
        left = self._parse_factor()
        while True:
            operator = self._peek_operator({"×", "÷"})
            if operator is None:
                return left
            self._read_operator()
            right = self._parse_factor()
            left = Expression.binary(operator, left, right)

    def _parse_factor(self) -> Expression:
        self._skip_spaces()
        if self.position >= len(self.text):
            raise ParseError("表达式不完整")
        if self.text[self.position] == "(":
            self.position += 1
            expression = self._parse_expression()
            self._skip_spaces()
            if self.position >= len(self.text) or self.text[self.position] != ")":
                raise ParseError("缺少右括号")
            self.position += 1
            return expression
        if self.text[self.position].isdigit():
            return Expression.leaf(self._read_number())
        raise ParseError(f"无法识别的表达式内容: {self.text[self.position:]}")

    def _read_number(self) -> Rational:
        self._skip_spaces()
        start = self.position
        while self.position < len(self.text) and self.text[self.position].isdigit():
            self.position += 1
        whole_or_numerator = int(self.text[start:self.position])

        self._skip_spaces()
        if self.position < len(self.text) and self.text[self.position] in {"’", "'"}:
            self.position += 1
            numerator = self._read_integer()
            self._expect("/")
            denominator = self._read_integer()
            if denominator == 0:
                raise ParseError("分母不能为 0")
            if numerator >= denominator:
                raise ParseError("带分数的分数部分必须小于 1")
            return Rational.from_parts(whole_or_numerator * denominator + numerator, denominator)

        if self.position < len(self.text) and self.text[self.position] == "/":
            self.position += 1
            denominator = self._read_integer()
            return Rational.from_parts(whole_or_numerator, denominator)

        return Rational.from_parts(whole_or_numerator)

    def _read_integer(self) -> int:
        self._skip_spaces()
        start = self.position
        while self.position < len(self.text) and self.text[self.position].isdigit():
            self.position += 1
        if start == self.position:
            raise ParseError("缺少整数")
        return int(self.text[start:self.position])

    def _expect(self, character: str) -> None:
        self._skip_spaces()
        if self.position >= len(self.text) or self.text[self.position] != character:
            raise ParseError(f"缺少字符: {character}")
        self.position += 1

    def _skip_spaces(self) -> None:
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1

    def _peek_operator(self, operators: set[str]) -> str | None:
        self._skip_spaces()
        if self.position >= len(self.text):
            return None
        character = self.text[self.position]
        if character == "−":
            character = "-"
        if character in operators:
            return character
        return None

    def _read_operator(self) -> None:
        self._skip_spaces()
        if self.position < len(self.text):
            self.position += 1


def parse_expression(text: str) -> Expression:
    try:
        return ExpressionParser(text).parse()
    except (ParseError, RationalError, ExpressionError) as exc:
        if isinstance(exc, ParseError):
            raise
        raise ParseError(str(exc)) from exc
