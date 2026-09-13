# 论文查重（Paper Plagiarism Checker）

> 软件工程导论 · 第一次个人编程作业
> 语言：Python 3 · 入口文件：`main.py`

## 一、功能说明

给定两个文本文件（原文、抄袭版论文），计算二者的重复率，
并把结果（保留两位小数）写入指定的答案文件。

命令行用法：

```bash
python main.py <原文文件> <抄袭版论文文件> <答案文件>
```

示例：

```bash
python main.py C:\tests\orig.txt C:\tests\orig_add.txt C:\tests\ans.txt
```

## 二、运行环境

- Python 3.8 及以上（开发环境为 Python 3.12）
- 运行程序本身**不需要任何第三方库**，`requirements.txt` 中没有运行时依赖
- 单元测试与覆盖率统计是可选功能，依赖见 `requirements-dev.txt`

## 三、目录结构

```
.
├── main.py                    # 程序入口，解析命令行参数并串联各模块
├── requirements.txt           # 运行时依赖（无第三方库）
├── requirements-dev.txt       # 开发/测试依赖
├── pyproject.toml             # ruff 代码检查与格式化配置
├── .vscode/                   # VS Code 项目配置（解释器、测试发现）
├── src/
│   ├── config.py              # 全局常量（n-gram 长度、小数位、输出单位）
│   ├── exceptions.py          # 自定义异常
│   ├── text_utils.py          # 文本清洗、n-gram 切分、词频统计
│   ├── file_io.py             # 文件读取（多编码）与写入
│   └── similarity.py          # 余弦相似度计算与结果格式化
├── tests/                     # 单元测试（unittest / pytest 均可运行）
├── tools/
│   ├── coverage_report.py     # 用标准库统计语句覆盖率
│   ├── performance_report.py  # cProfile 热点分析 + 优化对比 + 图表数据
│   └── render_chart.ps1       # 把热点数据渲染成 PNG 柱状图
└── docs/                      # PSP 表格、博客稿、性能与覆盖率报告
```

## 四、算法说明

采用「字符 n-gram + 词频向量 + 余弦相似度」：

1. 清洗文本：只保留中英文和数字，统一小写、全角转半角；
2. 切分：把连续文本切成字符二元组（bigram）；
3. 统计：得到每个二元组的出现次数，形成词频向量；
4. 相似度：计算两个向量的余弦相似度，取值 0~1。

选择字符 n-gram 而不是分词的原因：中文没有空格，分词需要额外词典；
字符 n-gram 无需依赖、对中英文混排同样有效，且能保留局部语序信息。

## 五、输出格式说明

答案文件中的数值默认是 **0~1 的相似度**，保留两位小数，例如 `0.86`。

需求没有明确要求是 0~1 还是 0~100。如果评测给出的答案用的是百分数，
只需要把 `src/config.py` 里的 `OUTPUT_AS_PERCENTAGE` 改成 `True` 即可，
输出会变成 `86.00` 这样的形式。

## 六、测试

```bash
# 运行全部单元测试（标准库，无需安装任何东西）
python -m unittest discover -s tests -t .

# 如果你装了 pytest
python -m pytest tests -v

# 统计覆盖率（标准库实现，不依赖 coverage 包）
python tools/coverage_report.py
```

## 七、性能分析

```bash
python tools/performance_report.py
powershell -ExecutionPolicy Bypass -File tools/render_chart.ps1
```

结果写入 `docs/profile.txt`、`docs/benchmark.txt`、`docs/profile.svg`、`docs/profile.png`。
