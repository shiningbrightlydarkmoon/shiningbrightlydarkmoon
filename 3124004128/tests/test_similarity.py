"""``similarity`` 模块的单元测试。"""

import math
import unittest
from unittest import mock

from src.exceptions import EmptyContentError
from src.similarity import SimilarityCalculator, cosine_similarity, format_score


class CosineSimilarityTest(unittest.TestCase):
    """测试余弦相似度函数。"""

    def test_identical_vectors_return_one(self):
        vector = {"a": 1, "b": 2}
        self.assertAlmostEqual(cosine_similarity(vector, vector), 1.0)

    def test_no_overlap_returns_zero(self):
        self.assertEqual(cosine_similarity({"a": 1}, {"b": 1}), 0.0)

    def test_empty_vector_returns_zero(self):
        self.assertEqual(cosine_similarity({}, {"a": 1}), 0.0)

    def test_result_is_symmetric(self):
        vector_a = {"x": 1, "y": 2}
        vector_b = {"x": 2, "z": 1}
        self.assertAlmostEqual(
            cosine_similarity(vector_a, vector_b),
            cosine_similarity(vector_b, vector_a),
        )

    def test_known_value(self):
        score = cosine_similarity({"a": 1, "b": 1}, {"a": 1})
        self.assertAlmostEqual(score, 1 / math.sqrt(2), places=6)

    def test_zero_weight_vector_returns_zero(self):
        # 权重全为 0 时向量长度为 0，应返回 0.0 而不是抛除零错误。
        self.assertEqual(cosine_similarity({"a": 0}, {"a": 1}), 0.0)


class SimilarityCalculatorTest(unittest.TestCase):
    """测试查重计算器。"""

    def setUp(self):
        self.calculator = SimilarityCalculator()

    def test_identical_text_returns_one(self):
        text = "今天是星期天，天气晴。"
        self.assertAlmostEqual(self.calculator.similarity(text, text), 1.0)

    def test_unrelated_text_returns_zero(self):
        score = self.calculator.similarity("苹果香蕉", "电脑手机")
        self.assertEqual(score, 0.0)

    def test_assignment_example_is_high_but_not_one(self):
        original = "今天是星期天，天气晴，今天晚上我要去看电影。"
        copy = "今天是周天，天气晴朗，我晚上要去看电影。"
        score = self.calculator.similarity(original, copy)
        self.assertGreater(score, 0.5)
        self.assertLess(score, 1.0)

    def test_one_side_empty_returns_zero(self):
        self.assertEqual(self.calculator.similarity("今天天气晴", ""), 0.0)

    def test_both_sides_empty_raises(self):
        with self.assertRaises(EmptyContentError):
            self.calculator.similarity("", "")

    def test_punctuation_only_is_treated_as_empty(self):
        self.assertEqual(self.calculator.similarity("今天天气晴", "，。！？"), 0.0)

    def test_n_gram_size_is_configurable(self):
        calculator = SimilarityCalculator(n_gram_size=1)
        self.assertAlmostEqual(calculator.similarity("天气晴", "天气晴"), 1.0)

    def test_score_is_symmetric(self):
        left = "今天是星期天，天气晴。"
        right = "今天是周天，天气晴朗。"
        self.assertAlmostEqual(
            self.calculator.similarity(left, right),
            self.calculator.similarity(right, left),
        )


class FormatScoreTest(unittest.TestCase):
    """测试结果格式化。"""

    def test_default_format_keeps_two_decimals(self):
        self.assertEqual(format_score(0.8567), "0.86")

    def test_one_is_formatted_as_1_00(self):
        self.assertEqual(format_score(1.0), "1.00")

    def test_percentage_mode(self):
        with mock.patch("src.similarity.OUTPUT_AS_PERCENTAGE", True):
            self.assertEqual(format_score(0.8567), "85.67")
