作业地址：https://github.com/shiningbrightlydarkmoon/shiningbrightlydarkmoon/tree/main/3124004128
# 第一次个人编程作业：论文查重

## 一、PSP 表格（开发前估计）

完整表格见仓库 `docs/PSP.md`，此处摘录估计值：

| 阶段 | 预估耗时（分钟） |
| --- | --- |
| 计划（Estimate） | 20 |
| 需求分析 | 60 |
| 生成设计 | 40 |
| 设计复审 | 20 |
| 代码规范 | 20 |
| 具体设计 | 50 |
| 具体编码 | 180 |
| 代码复审 | 40 |
| 测试 | 120 |
| 报告 | 70 |
| **合计** | **620** |

## 二、计算模块接口的设计与实现过程

### 2.1 代码如何组织

项目按「入口 / 核心算法 / 工具」三层拆分，核心算法完全不接触文件和命令行，因此可以脱离真实环境单独做单元测试。

| 文件 | 职责 | 关键函数 / 类 |
| --- | --- | --- |
| `main.py` | 入口：解析参数、串联流程、统一异常处理 | `parse_args`、`run`、`main` |
| `src/config.py` | 全局常量 | `N_GRAM_SIZE`、`DECIMAL_PLACES`、`OUTPUT_AS_PERCENTAGE` |
| `src/exceptions.py` | 自定义异常 | `PlagiarismError` 及 4 个子类 |
| `src/text_utils.py` | 文本清洗与分词 | `clean_text`、`iter_ngrams`、`make_ngrams`、`count_ngrams` |
| `src/file_io.py` | 文件读写（多编码） | `read_text`、`write_answer` |
| `src/similarity.py` | 相似度计算与格式化 | `cosine_similarity`、`SimilarityCalculator`、`format_score` |

调用关系：

```mermaid
flowchart LR
    A[命令行参数] --> B[parse_args 校验参数]
    B --> C[read_text 读取原文]
    B --> D[read_text 读取抄袭版]
    C --> E[SimilarityCalculator.similarity]
    D --> E
    E --> F[clean_text 清洗文本]
    F --> G[count_ngrams 生成词频向量]
    G --> H[cosine_similarity 余弦相似度]
    H --> I[format_score 保留两位小数]
    I --> J[write_answer 写入答案文件]
```

### 2.2 算法的关键

核心算法是 **字符 n-gram + 词频向量 + 余弦相似度**，分四步：

1. **清洗**：用正则 `[a-zA-Z0-9\u4e00-\u9fff\u3400-\u4dbf]+` 只保留中英文和数字，同时用 `unicodedata.normalize("NFKC", ...)` 把全角字母数字折叠成半角、统一小写。这样「Ａ」和「A」不会被认为是两个不同的词。
2. **切分**：把清洗后的字符串切成**长度为 2 的字符 n-gram（bigram）**。例如「天气晴朗」→ `天气 / 气晴 / 晴朗`。
3. **向量化**：用 `collections.Counter` 统计每个 bigram 的出现次数，得到词频向量。
4. **相似度**：用余弦相似度衡量两个向量的夹角：

   ```text
   cos(A, B) = (A · B) / (|A| × |B|)
   ```

   取值范围 0~1，对文本长度不敏感，很适合「增删改」型抄袭的检测。

**为什么用字符 n-gram 而不是分词？**
中文没有天然的空格，分词必须依赖词典（如 jieba）。而评测环境不一定能联网安装第三方库，一旦装不上就有 0 分的风险。字符 n-gram 不需要任何词典，对中英文混排同样有效，还能保留局部语序信息，因此更稳妥。

### 2.3 独到之处

- **零第三方依赖**：核心算法只用标准库，`requirements.txt` 里没有任何运行时依赖，离线评测环境也能直接跑。
- **多编码兼容**：`read_text` 会依次尝试 `utf-8-sig / utf-8 / gb18030 / gbk / utf-16`，兼容中文 Windows 上常见的各种编码。
- **性能有针对性优化**：`count_ngrams` 对最常用的 `n = 2` 走 `zip` 快速路径，词频统计改用 C 实现的 `Counter`，实测词频统计快约 1.7 倍（见第三节）。
- **异常分层**：所有可预期错误都继承自 `PlagiarismError`，入口处统一捕获，既能给出友好提示，又方便单元测试精确断言。

### 2.4 代码质量分析

用 `ruff` 对全部源码做静态检查。项目支持 Python 3.8 起，所以把目标版本写进`pyproject.toml`，让工具的建议和实际运行环境保持一致，而不是盲目套用新语法：

```bash
python -m pip install ruff
python -m ruff check .           # 静态检查
python -m ruff format --check .  # 格式检查
```

检查结果：

```text
All checks passed!
```

覆盖的规则集：

| 规则集 | 含义 |
| --- | --- |
| `E` / `W` / `F` | 风格问题、未使用的变量与导入 |
| `I` | 导入顺序 |
| `N` | 命名规范 |
| `UP` | 语法现代化 |
| `B` | 常见缺陷 |
| `SIM` / `C4` | 可简化的写法 |
| `ISC` | 字符串拼接 |

实际修掉的问题包括：未使用的导入、冗余的 `open` 模式参数、可以合并的嵌套 `with` 语句、隐式字符串拼接等，最终告警数为 0 。完整输出见 `docs/lint.txt`。

## 三、计算模块接口部分的性能改进

### 3.1 性能分析

用 `cProfile` 对一段 20 万字符的文本做查重，热点函数如下（图表由 `tools/performance_report.py` 自动生成，原图见 `docs/profile.png`）：

![profile](https://img2024.cnblogs.com/blog/3846699/202609/3846699-20260913122055543-391754150.png)


| 函数 | 累计耗时 |
| --- | --- |
| `similarity` | 55.92 ms |
| `build_vector` | 54.37 ms |
| `count_ngrams` | 50.53 ms |
| `clean_text` | 3.78 ms |
| `cosine_similarity` | 1.54 ms |

### 3.2 瓶颈定位

可以看到，**耗时几乎全部集中在「文本 → 词频向量」这一步**（`build_vector` 占 54 ms），而真正的余弦相似度计算只有 1.5 ms。进一步拆解发现瓶颈有两个：

1. 用 Python 手写循环统计词频，比 C 实现的 `collections.Counter` 慢；
2. 先用列表推导式生成 20 万个 bigram 的**列表**，再交给 Counter，多了一次完整列表的内存分配。

### 3.3 改进思路与效果

| 改进点 | 改进前 | 改进后 |
| --- | --- | --- |
| 词频统计 | 手写 `for` 循环 + `dict.get` | `collections.Counter`（C 实现） |
| n-gram 生成 | 列表推导式，一次性建列表 | `n=2` 时用 `zip` 配对拼接；否则用生成器 |

实测结果（20 万字符，见 `docs/benchmark.txt`）：

| 指标（20 万字符） | 改进前 | 改进后 | 提升 |
| --- | --- | --- | --- |
| 词频统计 | 12.1 ms（手写 `for` 循环） | 7.3 ms（`Counter`） | 约 1.7x |

优化后一次完整查重耗时 **69.3 ms**，其中 `count_ngrams` 累计约 51 ms，瓶颈已经压到「C 实现的计数」本身；在 20 万字符规模下仍远低于作业要求的 5 秒上限。

## 四、计算模块部分单元测试展示

### 4.1 测试设计思路

测试用标准库 `unittest` 编写（`pytest` 也能直接运行），共 **56 个测试用例**，覆盖以下场景：

- **正常路径**：完全相同的文本 → 1.00；完全不相关的文本 → 0.00；对文本做增删改后 → 介于两者之间；
- **边界条件**：空文本、纯标点、单个字符、全角字符、超长 n；
- **编码兼容**：UTF-8、带 BOM 的 UTF-8、GBK；
- **磁盘异常**：文件不存在、路径是目录、路径为空、写入目录不存在；
- **命令行**：参数过少 / 过多、文件缺失、运行成功；
- **对称性**：`similarity(a, b) == similarity(b, a)`。

### 4.2 测试代码示例

```python
class SimilarityCalculatorTest(unittest.TestCase):
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

    def test_both_sides_empty_raises(self):
        with self.assertRaises(EmptyContentError):
            self.calculator.similarity("", "")
```

```python
class ReadTextTest(unittest.TestCase):
    def test_read_gbk(self):
        path = self._write("gbk.txt", "中文内容", "gbk")
        self.assertEqual(read_text(path), "中文内容")

    def test_missing_file_raises(self):
        with self.assertRaises(FileReadError):
            read_text(os.path.join(self.temp_dir.name, "not_here.txt"))
```

运行方式：

```bash
python -m unittest discover -s tests -t .
# 或
python -m pytest tests -v
```
截图：
![29e2651bbcad19f7b4d62a0e808d9f49](https://img2024.cnblogs.com/blog/3846699/202609/3846699-20260913122248086-2112645272.png)


### 4.3 覆盖率

用 VS Code 的「测试覆盖率」面板查看，也可以直接用 coverage 命令行统计：

```bash
python -m coverage run --branch --source=src,main -m unittest discover -s tests -t .
python -m coverage report -m      # 终端摘要（含语句、分支覆盖率）
python -m coverage html           # 生成 htmlcov/index.html 可视化报告
```

VS Code 覆盖率面板的结果（面板中 `tests/` 目录同样为 100%，此处只列被测源码）：

| 文件 | 覆盖率 |
| --- | --- |
| `main.py` | 93.75% |
| `src/__init__.py` | 100.00% |
| `src/config.py` | 100.00% |
| `src/exceptions.py` | 100.00% |
| `src/file_io.py` | 95.65% |
| `src/similarity.py` | 100.00% |
| `src/text_utils.py` | 100.00% |
| **合计** | **98.97%** |

另外用 `coverage --branch` 复核了分支覆盖率：**语句覆盖率 98.5%，分支覆盖率 94.7%**（38 个分支只有 2 个未完全覆盖）。未覆盖的只有两处：`main.py` 的`if __name__ == "__main__"` 入口，以及 `file_io.py` 里一个极端磁盘错误分支。

> 项目另外内置了一个零依赖的统计脚本 `python tools/coverage_report.py`，
> 它的口径更严格（把 docstring 和类定义也计入语句），所以数值略低，约 89%；
> 博客中采用 VS Code / coverage 官方口径。

覆盖率截图：
![37f4b1af3ef93ceab61bef9ad0449bcc](https://img2024.cnblogs.com/blog/3846699/202609/3846699-20260913122145486-1444775456.png)

### 4.4 课堂样例实测

除了单元测试，还有一个测试文本的验证：`orig.txt` 是原文，其余 5 个文件是在原文基础上分别做了增、删、改的抄袭版，另外把原文和自身比一次作为基准校验。

| 对比文件 | 改动方式 | 输出重复率 |
| --- | --- | --- |
| `orig` vs `orig_0.8_add` | 随机插入干扰字 | 0.90 |
| `orig` vs `orig_0.8_del` | 随机删除字 | 0.90 |
| `orig` vs `orig_0.8_dis_1` | 打乱语序（幅度小） | 0.97 |
| `orig` vs `orig_0.8_dis_10` | 打乱语序（幅度中） | 0.91 |
| `orig` vs `orig_0.8_dis_15` | 打乱语序（幅度大） | 0.75 |
| `orig` vs `orig` | 自比（基准校验） | 1.00 |

结果有两点能说明算法是可靠的：

- **自比得到 1.00**，说明向量构建和余弦计算在基准情况下没有任何偏差；
- **改动越剧烈分数越低**：语序打乱幅度最小的 `dis_1` 还有 0.97，幅度最大的 `dis_15` 掉到 0.75。分数对抄袭程度是单调敏感的，不是一个随机数。

终端运行结果：
![image](https://img2024.cnblogs.com/blog/3846699/202609/3846699-20260914202414527-396278042.png)


## 五、计算模块部分异常处理说明

所有异常都继承自 `PlagiarismError`，`main.py` 在入口统一捕获，按类型返回不同退出码，保证程序不会异常崩溃。

| 异常类型 | 设计目标 | 触发场景 | 退出码 |
| --- | --- | --- | --- |
| `InvalidArgumentError` | 提示用户命令格式不对 | 命令行参数个数不是 3 个 | 2 |
| `FileReadError` | 区分「找不到文件」和「读不了文件」 | 路径不存在、路径是目录、编码无法识别 | 1 |
| `EmptyContentError` | 避免对空内容做无意义的比较 | 两篇文本清洗后都没有有效字符 | 1 |
| `OutputWriteError` | 提示答案文件无法写入 | 答案目录不存在、无写入权限 | 1 |

每个异常都配有单元测试，例如：

```python
# 场景：参数个数不对
def test_too_few_arguments_raises(self):
    with self.assertRaises(InvalidArgumentError):
        parse_args(["main.py", "orig.txt"])


# 场景：原文文件不存在
def test_missing_input_file_returns_1(self):
    original = self._write("orig.txt", "今天天气晴")
    missing = os.path.join(self.temp_dir.name, "missing.txt")
    self.assertEqual(run(["main.py", original, missing, answer]), 1)


# 场景：两篇文本都为空
def test_both_sides_empty_raises(self):
    with self.assertRaises(EmptyContentError):
        SimilarityCalculator().similarity("", "")


# 场景：答案目录不存在
def test_missing_directory_raises(self):
    with self.assertRaises(OutputWriteError):
        write_answer(os.path.join(self.temp_dir.name, "no_such_dir", "ans.txt"), "0.86")
```

## 六、PSP 表格（开发后实际）

| 阶段 | 预估耗时（分钟） | 实际耗时（分钟） |
| --- | --- | --- |
| 计划（Estimate） | 20 | 20 |
| 需求分析 | 60 | 90 |
| 生成设计 | 40 | 35 |
| 设计复审 | 20 | 15 |
| 代码规范 | 20 | 15 |
| 具体设计 | 50 | 45 |
| 具体编码 | 180 | 240 |
| 代码复审 | 40 | 30 |
| 测试 | 120 | 85 |
| 报告 | 70 | 75 |
| **合计** | **620** | **650** |

## 七、源代码管理与签入记录

项目用 Git 管理，按功能分 5 次提交，每一步都保证代码检查通过后再提交：

| 提交信息 | 内容 |
| --- | --- |
| `feat: 初始化项目结构与全局配置` | 目录结构、全局常量、异常类、依赖声明 |
| `feat: 实现文本清洗与 n-gram 分词` | `text_utils`：清洗、切分、词频统计 |
| `feat: 实现文件读写、余弦相似度计算与程序入口` | `file_io`、`similarity`、`main.py`，程序此时可端到端运行 |
| `test: 添加 56 个单元测试与覆盖率、性能分析工具` | `tests/`、`tools/` |
| `docs: 补充 README、PSP 表格与博客稿` | 文档与报告 |

仓库文件夹截图：

![image](https://img2024.cnblogs.com/blog/3846699/202609/3846699-20260913150738447-1896827058.png)


提交记录 Commits 截图：

![image](https://img2024.cnblogs.com/blog/3846699/202609/3846699-20260913150833892-299140633.png)




## 八、总结

这次作业最大的收获是**在「好用」和「稳」之间做取舍**：一开始想用 jieba 分词，、但考虑到评测环境可能装不上第三方库，最终选择了纯标准库的字符 n-gram 方案。虽然精度上未必比分词方案更好，但它零依赖、结果稳定、可复现，风险更低。

另外，为了在不装 `coverage` 包的情况下拿到覆盖率，我读源码研究了标准库 `trace`的行为，发现它在「只有 docstring 和类定义」的模块上会漏记行号，于是自己用`sys.settrace` 写了一个极简行覆盖率工具——这个过程让我对 Python 的执行模型有了更直观的理解。