[English](wiki-recall.md) · [한국어](wiki-recall-ko.md) · [日本語](wiki-recall-ja.md) · **中文** · [Español](wiki-recall-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# wiki-recall

把 wiki 已经知道的内容拉进回答里，而不是重新推导一遍。

## 在 Claude 中使用

什么都不用说：钩子会在每条消息时搜索 wiki。想深入到附上的那几行之外，可以问“我们关于 X 是怎么决定的？”。

## 它做什么

1. 对每条消息，钩子会附上明显相关页面的路径和关键行——至少有两个共同的词，并覆盖问题 40% 的权重。不相关的消息什么也不附。
2. 要深入时，Claude 会读这些页面。当整个 wiki 很小（30,000 个字符或更少）时，它会全部读完（CAG）；否则挑出最合适的页面（RAG：BM25、问题覆盖度、图中的相邻页面）。
3. 韩文按两个字一组进行匹配；单字词只有在单独出现时才算数。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `recall.py "question" [--mode auto\|cag\|rag] [--top 3] [--min-coverage 0.4]` | 搜索 wiki |

停用词、助词和常见片段都是 `data/` 中的数据文件。`WIKI_RECALL_MIN_COVERAGE` 用来修改阈值。

## 背后的钩子检查

`wiki-recall` 钩子检查在每条消息时运行。

## 局限

附上的行是搜索挑出的摘录。引用之前请先打开页面。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
