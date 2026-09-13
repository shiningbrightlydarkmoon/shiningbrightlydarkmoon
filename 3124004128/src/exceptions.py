"""自定义异常。

把"参数错误""文件读不了""内容为空"等可预期的错误单独定义，
一方面让 ``main.py`` 能统一捕获并给出友好提示，
另一方面让单元测试可以精确断言具体的错误类型。
"""


class PlagiarismError(Exception):
    """本程序所有自定义异常的基类。"""


class InvalidArgumentError(PlagiarismError):
    """命令行参数个数或格式不正确。"""


class FileReadError(PlagiarismError):
    """文件不存在、不是普通文件、无读取权限，或编码无法识别。"""


class EmptyContentError(PlagiarismError):
    """文件内容为空，去掉标点和空白后没有可比较的有效字符。"""


class OutputWriteError(PlagiarismError):
    """答案文件所在目录不存在或无法写入。"""
