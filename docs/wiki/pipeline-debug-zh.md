[English](pipeline-debug.md) · [한국어](pipeline-debug-ko.md) · [日本語](pipeline-debug-ja.md) · **中文** · [Español](pipeline-debug-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# pipeline-debug

当代码出错或给出错误结果时，沿着流水线往回追查故障，而不是在问题冒出来的那一行打补丁。

## 在 Claude 中使用

说“找出这个错误的原因”。对于错误、traceback 和失败的运行，`skill-match` 会指出这个技能。

## 它做什么

1. 画出数据经过的各个阶段。
2. 检查每个阶段的输入和输出——数量、列、几个真实的值——是否符合预期。
3. 第一个输出出错的阶段就是原因所在；报错通常出现在更下游。
4. 在那个阶段复现故障，用一个会失败的检查把它固定下来，在那里修复，然后把后面的每个阶段都重新运行一遍。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `probe.py [--rows N] FILE ...` | 显示在阶段之间传递的文件的行数、列、空值和开头几行 |

## 局限

它需要中间文件；一条在阶段之间什么都不保存的流水线，需要在保存这些文件的情况下重新运行。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
