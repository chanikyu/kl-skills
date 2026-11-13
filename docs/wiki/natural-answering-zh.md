[English](natural-answering.md) · [한국어](natural-answering-ko.md) · [日本語](natural-answering-ja.md) · **中文** · [Español](natural-answering-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# natural-answering

写出读者第一遍就能跟上的回答、报告和文档，办法是拒绝跳过解释中的任何一环。

## 在 Claude 中使用

什么都不用说：`answer-check` 钩子检查会读每一个回答。

## 它做什么

1. 有八样东西绝不跳过：术语第一次出现时的含义、从数字到结论的那一步、数字是和什么比较的、为什么要做这件事、句子的主语、用日常说法表达的单位、一个计数背后的具体项，以及用平实的话转述审查者或工具说了什么。
2. 第一句话回答被问到的问题。
3. 一个回答要能放在一屏之内；更长的内容就写成文档，并附一段简短摘要。
4. 修改代码之后，报告按六步来写：结果、摘要、改动、验证、问题与局限、后续工作。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `check_prose.py <files>` | 标出未定义的术语和缩写、过长的句子以及其他遗漏 |

规则是 `data/` 中的数据；工作报告和文档的骨架在 `references/` 中。

## 背后的钩子检查

当回答有以下缺漏时，`answer-check` 会把它退回一次：同一个问题被再问了一遍、一个回合改了文件却没有六步工作报告、回答超过一屏，或者行文检查发现了问题。`prose-check` 负责读 wiki 页面。

## 局限

这些检查以韩文为主。韩文以外的文本只检查未定义的缩写和过长的句子。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
