"""相似度计算核心模块。

采用「字符 n-gram + 词频向量 + 余弦相似度」的方案：

1. 把两篇文本清洗、切成字符二元组；
2. 统计每个二元组的出现次数，得到词频向量；
3. 计算两个向量的余弦相似度，取值 0~1。

选择这个方案的原因：

- 中文没有空格分词，字符 n-gram 不需要额外词典，天然适配中英文混排；
- 余弦相似度对文本长度不敏感，适合"增删改"后的抄袭检测；
- 只用标准库，评测环境不需要联网装包，结果稳定可复现。
"""

import math
from typing import Dict

from .config import DECIMAL_PLACES, N_GRAM_SIZE, OUTPUT_AS_PERCENTAGE
from .exceptions import EmptyContentError
from .text_utils import clean_text, count_ngrams


def cosine_similarity(vector_a: Dict[str, int], vector_b: Dict[str, int]) -> float:
    """计算两个词频向量的余弦相似度。

    公式：``cos = (A·B) / (|A| * |B|)``

    Args:
        vector_a: 第一个词频向量。
        vector_b: 第二个词频向量。

    Returns:
        0~1 之间的相似度。任意一方为空向量时返回 0.0。
    """
    if not vector_a or not vector_b:
        return 0.0

    # 只在较短的向量上遍历并查另一个字典，减少循环次数。
    if len(vector_a) > len(vector_b):
        vector_a, vector_b = vector_b, vector_a

    dot_product = 0
    for token, weight in vector_a.items():
        dot_product += weight * vector_b.get(token, 0)

    norm_a = math.sqrt(sum(weight * weight for weight in vector_a.values()))
    norm_b = math.sqrt(sum(weight * weight for weight in vector_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def format_score(score: float) -> str:
    """把相似度格式化成写入答案文件的字符串。

    Args:
        score: 0~1 的相似度。

    Returns:
        保留 ``DECIMAL_PLACES`` 位小数的字符串。
    """
    value = score * 100 if OUTPUT_AS_PERCENTAGE else score
    return f"{value:.{DECIMAL_PLACES}f}"


class SimilarityCalculator:
    """论文查重计算器。

    把「预处理 -> 向量化 -> 相似度」串成一个可复用的对象，
    n-gram 长度在构造时可调，方便做参数对比实验。
    """

    def __init__(self, n_gram_size: int = N_GRAM_SIZE) -> None:
        self.n_gram_size = n_gram_size

    def build_vector(self, text: str) -> Dict[str, int]:
        """把一段文本转成词频向量。"""
        return count_ngrams(clean_text(text), self.n_gram_size)

    def similarity(self, original: str, copy: str) -> float:
        """计算原文与抄袭版论文的相似度。

        Args:
            original: 原文内容。
            copy: 抄袭版论文内容。

        Returns:
            0~1 的相似度。

        Raises:
            EmptyContentError: 两篇文本清洗后都没有有效字符。
        """
        vector_original = self.build_vector(original)
        vector_copy = self.build_vector(copy)
        if not vector_original and not vector_copy:
            raise EmptyContentError("两篇文本都没有可比较的有效内容")
        return cosine_similarity(vector_original, vector_copy)
