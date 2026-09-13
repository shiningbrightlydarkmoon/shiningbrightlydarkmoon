"""文件读取与写入。

把所有磁盘 I/O 集中在这里，核心算法不直接接触文件，
这样算法可以脱离真实文件单独做单元测试。
"""

import os
from typing import List, Optional

from .exceptions import FileReadError, OutputWriteError

# 依次尝试的编码。中文 Windows 上常见的编码都覆盖到了。
# 顺序很重要：优先 utf-8，再退回兼容 gbk 的 gb18030，最后才是 gbk/utf-16。
ENCODINGS: List[str] = ["utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"]


def read_text(path: str) -> str:
    """按多种编码依次尝试读取文本文件。

    Args:
        path: 文件绝对路径。

    Returns:
        文件内容字符串。

    Raises:
        FileReadError: 路径不存在、不是普通文件、无读取权限，
            或所有候选编码都解码失败。
    """
    if not path:
        raise FileReadError("文件路径不能为空")
    if not os.path.exists(path):
        raise FileReadError(f"文件不存在：{path}")
    if not os.path.isfile(path):
        raise FileReadError(f"路径不是文件：{path}")

    last_error: Optional[Exception] = None
    for encoding in ENCODINGS:
        try:
            with open(path, encoding=encoding) as handle:
                return handle.read()
        except UnicodeDecodeError as error:
            last_error = error
            continue
        except OSError as error:
            raise FileReadError(f"读取文件失败：{path}（{error}）") from error

    raise FileReadError(f"无法识别文件编码：{path}") from last_error


def write_answer(path: str, content: str) -> None:
    """把结果写入答案文件（UTF-8 编码，末尾带换行）。

    Args:
        path: 答案文件路径。
        content: 已经格式化好的文本内容。

    Raises:
        OutputWriteError: 路径为空、所在目录不存在，或没有写入权限。
    """
    if not path:
        raise OutputWriteError("答案文件路径不能为空")
    directory = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(directory):
        raise OutputWriteError(f"答案文件所在目录不存在：{directory}")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.write("\n")
    except OSError as error:
        raise OutputWriteError(f"写入答案文件失败：{path}（{error}）") from error
