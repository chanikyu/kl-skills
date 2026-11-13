[English](graph-doc-memory.md) · [한국어](graph-doc-memory-ko.md) · [日本語](graph-doc-memory-ja.md) · **中文** · [Español](graph-doc-memory-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# graph-doc-memory

把整个 wiki 变成一个图数据库，并在浏览器中以交互式图的形式打开——只在你要求时才这样做。

## 在 Claude 中使用

说“给我看看 wiki 图”。

## 它做什么

1. `<topic>/wiki/` 下的每个页面是一个节点；每个 `[[link]]` 或 `[text](page.md)` 是一条连线。指向尚不存在页面的链接会以虚线圆圈留在图中——这些是值得填补的空缺。
2. 构建会写出 `~/llm-wiki-docs/.graph/graph.json` 和一个自包含的 `viewer.html`，它通过 `file://` 打开，不需要服务器。
3. 查看器提供：搜索、孤立页面和缺失页面的显示开关、节点大小、连线粗细、四种力，以及围绕所选节点的局部图。点击一个节点，可以看到它的路径、链接和反向链接。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `open-graph.sh [--root DIR] [--out DIR] [--no-build]` | 重建图并打开查看器 |
| `build_graph.py [--root ROOT] [--out OUT] [--quiet]` | 只重建，不打开 |

## 背后的钩子检查

写入 wiki 页面时，`wiki-graph` 会重建图；回答结束时，`wiki-sync` 会捕捉 shell 中的编辑。

## 局限

它从不自行打开。图的连通程度取决于页面之间的链接。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
