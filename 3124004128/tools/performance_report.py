"""性能分析脚本。

会生成三份产物，可直接贴进博客：

- ``docs/profile.txt``：cProfile 输出的热点函数排名；
- ``docs/benchmark.txt``：优化前后（手写循环 vs Counter）的耗时对比；
- ``docs/profile.svg``：热点函数累计耗时柱状图。

用法::

    python tools/performance_report.py
"""

import cProfile
import io
import os
import pstats
import random
import sys
import time
from collections import Counter
from typing import Dict, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.similarity import SimilarityCalculator  # noqa: E402
from src.text_utils import clean_text, make_ngrams  # noqa: E402

# 用一批汉字随机拼出大文本，保证 n-gram 足够丰富，接近真实论文场景。
_VOCABULARY = (
    "论文查重算法设计原文文件抄袭版本输出重复率今天是星期天天气晴朗晚上要去看电影"
    "数据结构和算法分析设计模式软件工程单元测试性能优化代码规范需求分析"
)


def build_text(length: int, seed: int) -> str:
    """生成指定长度的伪随机中文文本。"""
    random.seed(seed)
    return "".join(random.choice(_VOCABULARY) for _ in range(length))


def naive_term_frequency(tokens: List[str]) -> Dict[str, int]:
    """优化前的实现：手写 Python 循环计数。"""
    frequencies: Dict[str, int] = {}
    for token in tokens:
        frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies


def measure(function, tokens: List[str], rounds: int = 5) -> float:
    """测量 ``function(tokens)`` 的平均耗时（秒）。"""
    start = time.perf_counter()
    for _ in range(rounds):
        function(tokens)
    return (time.perf_counter() - start) / rounds


def collect_hotspots(profiler: cProfile.Profile, limit: int = 10) -> List[Dict]:
    """从 profile 结果里挑出本项目内部累计耗时最高的函数。"""
    stats = pstats.Stats(profiler)
    entries = []
    for (filename, _lineno, function), values in stats.stats.items():
        call_count, _recursive, total_time, cumulative_time, _callers = values
        absolute = os.path.abspath(filename)
        # 只保留项目内的 Python 文件，排除标准库和内置函数（它们的文件名是 "~"）。
        if absolute.startswith(PROJECT_ROOT) and absolute.endswith(".py"):
            entries.append(
                {
                    "function": function,
                    "cumulative": cumulative_time,
                    "total": total_time,
                    "calls": call_count,
                }
            )
    entries.sort(key=lambda item: item["cumulative"], reverse=True)
    return entries[:limit]


def render_profile_text(profiler: cProfile.Profile, limit: int = 15) -> str:
    """把 cProfile 结果渲染成可读文本。"""
    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(limit)
    return stream.getvalue()


def render_svg(entries: List[Dict], output_path: str) -> None:
    """把热点函数画成横向柱状图（纯 SVG，不依赖任何绘图库）。"""
    row_height = 34
    width = 760
    height = 70 + row_height * len(entries)
    max_time = max((item["cumulative"] for item in entries), default=1.0) or 1.0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        (
            '<text x="12" y="30" font-size="18" font-weight="bold" fill="#111">'
            "查重程序热点函数累计耗时</text>"
        ),
    ]
    for index, item in enumerate(entries):
        y = 55 + index * row_height
        bar_width = int(item["cumulative"] / max_time * 430)
        parts.append(
            f'<text x="12" y="{y + 15}" font-size="13" fill="#333">{item["function"]}</text>'
        )
        parts.append(f'<rect x="200" y="{y}" width="{bar_width}" height="20" fill="#4f8cff"/>')
        parts.append(
            f'<text x="{208 + bar_width}" y="{y + 15}" font-size="12" fill="#555">'
            f"{item['cumulative'] * 1000:.2f} ms</text>"
        )
    parts.append("</svg>")

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def main() -> None:
    original = build_text(200000, seed=42)
    copy = original[:180000] + build_text(20000, seed=43)
    calculator = SimilarityCalculator()

    # 1) 整体耗时
    start = time.perf_counter()
    rounds = 3
    for _ in range(rounds):
        score = calculator.similarity(original, copy)
    average_seconds = (time.perf_counter() - start) / rounds

    # 2) cProfile 热点分析
    profiler = cProfile.Profile()
    profiler.enable()
    calculator.similarity(original, copy)
    profiler.disable()

    # 3) 优化前后对比
    cleaned = clean_text(original)
    tokens = make_ngrams(cleaned, 2)
    naive_seconds = measure(naive_term_frequency, tokens)
    counter_seconds = measure(Counter, tokens)

    os.makedirs(os.path.join(PROJECT_ROOT, "docs"), exist_ok=True)
    write_text(os.path.join(PROJECT_ROOT, "docs", "profile.txt"), render_profile_text(profiler))
    hotspots = collect_hotspots(profiler)
    render_svg(hotspots, os.path.join(PROJECT_ROOT, "docs", "profile.svg"))
    csv_lines = ["function,cumulative_ms,calls"]
    for item in hotspots:
        csv_lines.append(f"{item['function']},{item['cumulative'] * 1000:.3f},{item['calls']}")
    write_text(
        os.path.join(PROJECT_ROOT, "docs", "profile_data.csv"),
        "\n".join(csv_lines) + "\n",
    )

    benchmark_lines = [
        f"文本长度：{len(original)} 字符，n-gram 数：{len(tokens)}",
        f"完整查重耗时：{average_seconds * 1000:.1f} ms（平均 {rounds} 次）",
        f"相似度结果：{score:.4f}",
        "",
        f"词频统计 - 手写循环：{naive_seconds * 1000:.1f} ms",
        f"词频统计 - Counter ：{counter_seconds * 1000:.1f} ms",
        f"提速：{naive_seconds / counter_seconds:.1f}x",
    ]
    benchmark_text = "\n".join(benchmark_lines)
    write_text(os.path.join(PROJECT_ROOT, "docs", "benchmark.txt"), benchmark_text + "\n")

    print(benchmark_text)
    print("\n热点函数（前 10）：")
    for item in hotspots:
        print(f"  {item['function']:<20}{item['cumulative'] * 1000:>10.2f} ms")


if __name__ == "__main__":
    main()
