[English](graph-doc-memory.md) · [한국어](graph-doc-memory-ko.md) · **日本語** · [中文](graph-doc-memory-zh.md) · [Español](graph-doc-memory-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# graph-doc-memory

wiki 全体を1つのグラフデータベースにし、ブラウザで操作できるグラフとして開く。頼まれたときだけ動く。

## Claude での使い方

「wiki のグラフを見せて」と言う。

## 何をするか

1. `<topic>/wiki/` 以下のすべてのページがノードになり、すべての `[[link]]` や `[text](page.md)` がリンクになる。まだ存在しないページへのリンクは、破線の円としてグラフに残る。埋める価値のある穴である。
2. ビルドすると `~/llm-wiki-docs/.graph/graph.json` と、サーバーなしで `file://` から開ける単体完結の `viewer.html` が書き出される。
3. ビューアには、検索、孤立ページと未作成ページの表示切り替え、ノードの大きさ、リンクの太さ、4つの力、選んだノードの周りのローカルグラフがある。ノードをクリックすると、そのパス、リンク、バックリンクが表示される。

## ファイルとスクリプト

| スクリプト | すること |
| --- | --- |
| `open-graph.sh [--root DIR] [--out DIR] [--no-build]` | グラフを作り直してビューアを開く |
| `build_graph.py [--root ROOT] [--out OUT] [--quiet]` | 開かずに作り直す |

## このスキルを支えるフック

`wiki-graph` は wiki ページが書かれるとグラフを作り直す。`wiki-sync` は回答が終わるときにシェルでの編集を拾う。

## 制限

自分から開くことはない。グラフのつながりは、ページに書かれたリンクの分しかない。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
