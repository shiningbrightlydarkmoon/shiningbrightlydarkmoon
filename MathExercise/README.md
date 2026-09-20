# 小学四则运算题目生成器

这是一个使用 Python 实现的命令行程序，支持生成小学四则运算题和批改答案。


## 运行环境

- Python 3.10 或更高版本
- 不需要安装第三方依赖

## 生成题目

在项目根目录运行：

```powershell
python main.py -n 10 -r 10
```

参数说明：

- `-n`：生成题目的数量。
- `-r`：自然数、分数分子和分数分母的取值范围，结果不包含 `r`。
- 生成结果写入当前工作目录下的 `Exercises.txt`。
- `-r` 是必填参数；只提供 `-r` 时，默认生成 10 道题。

示例输出：

```text
1. 3/5 + 1/2 =
2. 2’3/8 × 4 =
3. 8 ÷ (2’1/4 - 1/2) =
```

## 批改答案

题目文件和答案文件都按行编号。答案文件可以写编号，也可以只写答案：

```text
1. 11/10
2. 19/2
3. 32/7
```

或者：

```text
11/10
19/2
32/7
```

运行：

```powershell
python main.py -e Exercises.txt -a Answers.txt
```

结果写入当前工作目录下的 `Grade.txt`：

```text
Correct: 5 (1, 3, 5, 7, 9)
Wrong: 5 (2, 4, 6, 8, 10)
```

## 测试

```powershell
python -m unittest discover -s tests -v
```

性能测试：

```powershell
python tools/benchmark.py --r 10 --counts 1000,5000,10000 --profile-count 10000
```

仓库中的 `examples/` 目录提供了 10 道示例题及对应的判分结果。

## 项目结构

```text
MathExercise/
├── main.py
├── src/
│   ├── rational.py       # 精确分数运算
│   ├── expression.py     # 表达式树、求值和去重标识
│   ├── parser.py         # 表达式解析
│   ├── generator.py      # 题目生成和约束
│   ├── exercise_io.py    # 文件和答案解析
│   ├── grader.py         # 判分
│   └── cli.py            # 命令行入口
├── tests/                # 自动化测试
├── examples/             # 10 道示例题、答案和判分结果
├── tools/
│   ├── benchmark.py      # 性能测试和 SVG 图表
│   └── validate.py       # 大规模题目文件校验
└── docs/                 # 设计、测试、PSP 和协作文档
```

## 规则说明

- 使用 `fractions.Fraction` 保证分数运算精确，不使用浮点数。
- 每道题最多 3 个运算符。
- 减法不允许产生负数。
- 除数不能为 0。
- 除法结果必须是大于 0 且小于 1 的真分数。
- 题目去重允许交换 `+` 和 `×` 的左右子树，但不会把整棵表达式树扁平化，因此 `1+2+3` 与 `3+(2+1)` 重复，而 `1+2+3` 与 `3+2+1` 不重复。
- `r` 很小时，合法且不重复的题目空间有限。如果请求数超过空间，程序会给出明确错误，而不是无限循环。

## 打包为 exe（可选）

如果作业要求必须提交 `Myapp.exe`，可以在安装 PyInstaller 后运行：

```powershell
pyinstaller --onefile --name Myapp main.py
```

生成文件位于 `dist/Myapp.exe`。核心代码不依赖 PyInstaller。
