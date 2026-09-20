from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction


class RationalError(ValueError):
    """Raised when a rational number cannot be parsed or is invalid."""


_MIXED_RE = re.compile(r"^\s*([+-]?\d+)\s*[’']\s*(\d+)\s*/\s*(\d+)\s*$")
_FRACTION_RE = re.compile(r"^\s*([+-]?\d+)\s*/\s*(\d+)\s*$")
_INTEGER_RE = re.compile(r"^\s*([+-]?\d+)\s*$")


@dataclass(frozen=True)
class Rational:
    """An exact non-floating-point rational number."""

    value: Fraction

    def __post_init__(self) -> None:
        if self.value.denominator == 0:
            raise RationalError("分母不能为 0")

    @classmethod
    def from_parts(cls, numerator: int, denominator: int = 1) -> "Rational":
        if denominator == 0:
            raise RationalError("分母不能为 0")
        return cls(Fraction(numerator, denominator))

    @classmethod
    def parse(cls, text: str) -> "Rational":
        raw = text.strip()
        if not raw:
            raise RationalError("不能解析空数字")

        mixed = _MIXED_RE.fullmatch(raw)
        if mixed:
            whole = int(mixed.group(1))
            numerator = int(mixed.group(2))
            denominator = int(mixed.group(3))
            if denominator == 0:
                raise RationalError("分母不能为 0")
            if numerator >= denominator:
                raise RationalError("带分数的分数部分必须小于 1")
            sign = -1 if whole < 0 else 1
            return cls(Fraction(sign * (abs(whole) * denominator + numerator), denominator))

        fraction = _FRACTION_RE.fullmatch(raw)
        if fraction:
            numerator = int(fraction.group(1))
            denominator = int(fraction.group(2))
            if denominator == 0:
                raise RationalError("分母不能为 0")
            return cls(Fraction(numerator, denominator))

        integer = _INTEGER_RE.fullmatch(raw)
        if integer:
            return cls(Fraction(int(integer.group(1)), 1))

        raise RationalError(f"无法识别数字: {text}")

    @property
    def numerator(self) -> int:
        return self.value.numerator

    @property
    def denominator(self) -> int:
        return self.value.denominator

    def is_zero(self) -> bool:
        return self.value == 0

    def is_positive(self) -> bool:
        return self.value > 0

    def is_proper(self) -> bool:
        return 0 < self.value < 1

    def __add__(self, other: object) -> "Rational":
        if not isinstance(other, Rational):
            return NotImplemented
        return Rational(self.value + other.value)

    def __sub__(self, other: object) -> "Rational":
        if not isinstance(other, Rational):
            return NotImplemented
        return Rational(self.value - other.value)

    def __mul__(self, other: object) -> "Rational":
        if not isinstance(other, Rational):
            return NotImplemented
        return Rational(self.value * other.value)

    def __truediv__(self, other: object) -> "Rational":
        if not isinstance(other, Rational):
            return NotImplemented
        if other.is_zero():
            raise ZeroDivisionError("不能除以 0")
        return Rational(self.value / other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Rational):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Rational):
            return NotImplemented
        return self.value <= other.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rational):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def format(self) -> str:
        """Return the format used by the assignment: 2/3 or 2’3/8."""

        numerator = self.numerator
        denominator = self.denominator
        sign = "-" if numerator < 0 else ""
        absolute = abs(numerator)
        whole, remainder = divmod(absolute, denominator)
        if remainder == 0:
            return f"{sign}{whole}"
        if whole:
            return f"{sign}{whole}’{remainder}/{denominator}"
        return f"{sign}{absolute}/{denominator}"

    def __str__(self) -> str:
        return self.format()
