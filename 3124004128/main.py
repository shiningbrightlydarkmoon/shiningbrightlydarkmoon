"""论文查重程序入口。

用法::

    python main.py <原文文件> <抄袭版论文文件> <答案文件>

从命令行读取三个文件的路径，计算重复率，
并把结果（保留两位小数）写入答案文件。
"""

import sys
from typing import List, Tuple

from src.exceptions import InvalidArgumentError, PlagiarismError
from src.file_io import read_text, write_answer
from src.similarity import SimilarityCalculator, format_score

USAGE = "用法：python main.py <原文文件> <抄袭版论文文件> <答案文件>"


def parse_args(argv: List[str]) -> Tuple[str, str, str]:
    """校验并解析命令行参数。

    Args:
        argv: 完整的命令行参数（含脚本名）。

    Returns:
        ``(原文路径, 抄袭版路径, 答案路径)``。

    Raises:
        InvalidArgumentError: 参数个数不为 3。
    """
    if len(argv) != 4:
        raise InvalidArgumentError(USAGE)
    return argv[1], argv[2], argv[3]


def run(argv: List[str]) -> int:
    """执行一次查重，返回进程退出码。

    Args:
        argv: 完整的命令行参数（含脚本名）。

    Returns:
        0 表示成功，1 表示运行出错，2 表示参数错误。
    """
    try:
        original_path, copy_path, answer_path = parse_args(argv)
        original_text = read_text(original_path)
        copy_text = read_text(copy_path)
        score = SimilarityCalculator().similarity(original_text, copy_text)
        write_answer(answer_path, format_score(score))
    except InvalidArgumentError as error:
        print(f"参数错误：{error}", file=sys.stderr)
        return 2
    except PlagiarismError as error:
        print(f"运行错误：{error}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    """脚本入口。"""
    sys.exit(run(sys.argv))


if __name__ == "__main__":
    main()
