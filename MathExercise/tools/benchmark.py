from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import ProblemGenerator  # noqa: E402


def measure(count: int, r: int, seed: int) -> tuple[float, int]:
    start = time.perf_counter()
    expressions = ProblemGenerator(r, seed=seed).generate(count)
    elapsed = time.perf_counter() - start
    unique_count = len({expression.canonical_key() for expression in expressions})
    if unique_count != count:
        raise RuntimeError(f"重复题目检测失败: {count=} {unique_count=}")
    return elapsed, unique_count


def profile_generation(count: int, r: int, seed: int) -> str:
    profiler = cProfile.Profile()
    profiler.enable()
    ProblemGenerator(r, seed=seed).generate(count)
    profiler.disable()
    output = io.StringIO()
    pstats.Stats(profiler, stream=output).sort_stats("cumulative").print_stats(12)
    return output.getvalue()


def write_svg(path: Path, results: list[tuple[int, float]]) -> None:
    width = 960
    height = 540
    left = 100
    right = 50
    top = 70
    bottom = 100
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_time = max(time_taken for _, time_taken in results)
    scale_max = max_time * 1.15

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">',
        '<rect width="960" height="540" fill="#ffffff"/>',
        '<text x="480" y="38" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold" fill="#1f2937">Exercise Generation Performance</text>',
        '<text x="480" y="62" text-anchor="middle" font-family="Arial" font-size="14" fill="#4b5563">ProblemGenerator generation time, r = 10</text>',
        f'<line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" y2="{top + chart_height}" stroke="#374151" stroke-width="1.5"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#374151" stroke-width="1.5"/>',
    ]

    for tick in range(6):
        value = scale_max * tick / 5
        y = top + chart_height - chart_height * tick / 5
        lines.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + chart_width}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-family="Arial" font-size="12" fill="#4b5563">{value:.3f}</text>'
        )

    bar_slot = chart_width / max(len(results), 1)
    bar_width = min(120.0, bar_slot * 0.58)
    colors = ["#2563eb", "#059669", "#d97706"]
    for index, (count, time_taken) in enumerate(results):
        x = left + index * bar_slot + (bar_slot - bar_width) / 2
        bar_height = chart_height * time_taken / scale_max
        y = top + chart_height - bar_height
        color = colors[index % len(colors)]
        lines.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="3" fill="{color}"/>'
        )
        lines.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-family="Arial" font-size="13" font-weight="bold" fill="#111827">{time_taken:.3f}s</text>'
        )
        lines.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{top + chart_height + 28}" text-anchor="middle" font-family="Arial" font-size="14" fill="#374151">{count}</text>'
        )

    lines.extend(
        [
            f'<text x="{left + chart_width / 2}" y="{height - 34}" text-anchor="middle" font-family="Arial" font-size="15" fill="#374151">Number of generated problems</text>',
            f'<text x="28" y="{top + chart_height / 2}" text-anchor="middle" transform="rotate(-90 28 {top + chart_height / 2})" font-family="Arial" font-size="15" fill="#374151">Time (seconds)</text>',
            '</svg>',
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_counts(raw: str) -> list[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values or any(value < 1 for value in values):
        raise argparse.ArgumentTypeError("counts 必须是逗号分隔的正整数")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark and profile exercise generation.")
    parser.add_argument("--r", type=int, default=10, help="range parameter")
    parser.add_argument("--counts", type=parse_counts, default=[1000, 5000, 10000])
    parser.add_argument("--profile-count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument(
        "--svg",
        type=Path,
        default=PROJECT_ROOT / "docs" / "performance.svg",
        help="output chart path",
    )
    args = parser.parse_args()

    results: list[tuple[int, float]] = []
    print(f"Benchmark: r={args.r}, seed={args.seed}")
    for count in args.counts:
        elapsed, unique_count = measure(count, args.r, args.seed)
        results.append((count, elapsed))
        print(f"count={count:>6} elapsed={elapsed:.6f}s unique={unique_count}")

    write_svg(args.svg, results)
    print(f"chart={args.svg.resolve()}")
    print()
    print(f"cProfile top functions for count={args.profile_count}:")
    print(profile_generation(args.profile_count, args.r, args.seed), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
