from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.exercise_io import read_exercises
from src.expression import Expression


def iter_leaves(expression: Expression):
    if expression.is_leaf:
        yield expression
        return
    yield from iter_leaves(expression.left)
    yield from iter_leaves(expression.right)


def validate(path: Path, r: int | None = None) -> None:
    items = read_exercises(path)
    errors: list[str] = []
    keys = {item.expression.canonical_key() for item in items}
    if len(keys) != len(items):
        errors.append(f"重复题目: 总数 {len(items)}, 唯一数 {len(keys)}")

    for item in items:
        expression = item.expression
        if expression.operator_count > 3:
            errors.append(f"第 {item.number} 题运算符超过 3 个")
        try:
            expression.evaluate()
        except Exception as exc:
            errors.append(f"第 {item.number} 题求值失败: {exc}")
        for leaf in iter_leaves(expression):
            if r is not None and leaf.value.denominator >= r:
                errors.append(f"第 {item.number} 题分母超出范围: {leaf.value}")
            if leaf.value.value < 0:
                errors.append(f"第 {item.number} 题出现负数: {leaf.value}")

    if errors:
        print("校验失败:")
        for error in errors[:20]:
            print(f"- {error}")
        if len(errors) > 20:
            print(f"- 还有 {len(errors) - 20} 个错误")
        raise SystemExit(1)

    print(f"校验通过: exercises={len(items)} unique={len(keys)} max_ops={max(item.expression.operator_count for item in items)}")


def _configure_utf8_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    _configure_utf8_output()
    parser = argparse.ArgumentParser(description="Validate an Exercises.txt file.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--r", type=int, default=None)
    args = parser.parse_args()
    validate(args.path, args.r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
