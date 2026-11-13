[English](llm-wiki-docs.md) · [한국어](llm-wiki-docs-ko.md) · [日本語](llm-wiki-docs-ja.md) · **中文** · [Español](llm-wiki-docs-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# llm-wiki-docs

把你学到的东西保存在 `~/llm-wiki-docs/<topic>/wiki/` 下的 wiki 里：一个主题一页，用你自己的话写，并附带索引和日志。

## 在 Claude 中使用

说“把这个放进 wiki”或“把这个保存到 wiki”。当消息提出这种要求时，`skill-match` 会指出这个技能。在值得保留的调研或分析之后，Claude 也会使用它。

## 它做什么

1. 来源原样保存在 `raw/` 中。wiki 页面是新写的文本，绝不是改过的来源。
2. 一个主题就是一页。同一主题会更新现有页面，而不是另起一个几乎重复的页面。
3. `index.md` 每个页面占一行，并且最先被搜索。
4. `log.md` 只能追加：`## [YYYY-MM-DD] ingest | title`。
5. 页面之间用 `[[page]]` 链接，每个论断都指向它的来源。

随代码变化而变化的内容留在项目自己的文档里；始终成立的内容放进 wiki。

## 文件和脚本

```text
~/llm-wiki-docs/<topic>/
  README.md      what the topic holds and where things go
  raw/           sources, untouched
  wiki/          pages, index.md, log.md
```

| 脚本 | 作用 |
| --- | --- |
| `new-topic.sh <topic> ["description"]` | 创建文件夹以及空的索引和日志，不会覆盖已有内容 |
| `index-add.py <topic> <page> <category> ["summary"]` | 把一个页面加入索引 |
| `log-append.py <topic> ingest\|query\|lint "title" [--pages --source --note]` | 追加一条日志 |
| `lint.py [topic]` | 找出没有列入索引或日志的页面、失效的链接和孤立页面 |

`LLM_WIKI_ROOT` 可以把根目录从 `~/llm-wiki-docs` 移到别处。

## 背后的钩子检查

`wiki-index-check` 标出没有列入索引的页面，`wiki-graph` 重新绘制图，`prose-check` 标出难读的地方，`wiki-sync` 在回答结束时捕捉从 shell 编辑的页面。

## 局限

wiki 只存在于你的机器上；不会同步到任何其他地方。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
