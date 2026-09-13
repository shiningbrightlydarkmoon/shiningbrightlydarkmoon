"""``text_utils`` 模块的单元测试。"""

import unittest
from collections import Counter

from src.text_utils import (
    clean_text,
    count_ngrams,
    iter_ngrams,
    make_ngrams,
    term_frequency,
    to_feature_vector,
)


class CleanTextTest(unittest.TestCase):
    """测试文本清洗函数。"""

    def test_removes_punctuation_and_whitespace(self):
        self.assertEqual(clean_text("今天是星期天，天气晴。"), "今天是星期天天气晴")

    def test_keeps_letters_and_digits(self):
        self.assertEqual(clean_text("abc 123!!"), "abc123")

    def test_lowercases_letters(self):
        self.assertEqual(clean_text("AbC"), "abc")

    def test_normalizes_fullwidth_characters(self):
        self.assertEqual(clean_text("ＡＢＣ１２３"), "abc123")

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(clean_text(""), "")

    def test_none_input_returns_empty_string(self):
        self.assertEqual(clean_text(None), "")

    def test_punctuation_only_returns_empty_string(self):
        self.assertEqual(clean_text("，。！？  \n\t"), "")


class MakeNgramsTest(unittest.TestCase):
    """测试 n-gram 切分。"""

    def test_bigram_split(self):
        self.assertEqual(make_ngrams("abcd", 2), ["ab", "bc", "cd"])

    def test_default_n_comes_from_config(self):
        self.assertEqual(make_ngrams("abcd"), ["ab", "bc", "cd"])

    def test_short_text_falls_back_to_single_characters(self):
        self.assertEqual(make_ngrams("a", 2), ["a"])

    def test_empty_text_returns_empty_list(self):
        self.assertEqual(make_ngrams("", 2), [])

    def test_invalid_n_raises_value_error(self):
        with self.assertRaises(ValueError):
            make_ngrams("abc", 0)


class TermFrequencyTest(unittest.TestCase):
    """测试词频统计。"""

    def test_counts_repeated_tokens(self):
        self.assertEqual(term_frequency(["a", "b", "a"]), {"a": 2, "b": 1})

    def test_empty_list_returns_empty_dict(self):
        self.assertEqual(term_frequency([]), {})


class ToFeatureVectorTest(unittest.TestCase):
    """测试「清洗 + 切分 + 词频」的完整流水线。"""

    def test_pipeline_produces_bigram_frequency(self):
        self.assertEqual(
            to_feature_vector("天气晴朗"),
            {"天气": 1, "气晴": 1, "晴朗": 1},
        )


class IterNgramsTest(unittest.TestCase):
    """测试生成器版本的 n-gram 切分。"""

    def test_generator_matches_list_version(self):
        self.assertEqual(list(iter_ngrams("abcd", 2)), make_ngrams("abcd", 2))

    def test_empty_text_yields_nothing(self):
        self.assertEqual(list(iter_ngrams("", 2)), [])


class CountNgramsTest(unittest.TestCase):
    """测试带快速路径的词频向量统计。"""

    def test_fast_path_matches_general_path(self):
        text = "今天是星期天天气晴"
        self.assertEqual(count_ngrams(text, 2), Counter(make_ngrams(text, 2)))

    def test_count_values(self):
        self.assertEqual(
            count_ngrams("天气晴朗", 2),
            {"天气": 1, "气晴": 1, "晴朗": 1},
        )

    def test_repeated_ngram_is_counted(self):
        self.assertEqual(count_ngrams("哈哈哈", 2)["哈哈"], 2)
