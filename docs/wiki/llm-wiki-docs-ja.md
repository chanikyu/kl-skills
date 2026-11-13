[English](llm-wiki-docs.md) · [한국어](llm-wiki-docs-ko.md) · **日本語** · [中文](llm-wiki-docs-zh.md) · [Español](llm-wiki-docs-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# llm-wiki-docs

学んだことを `~/llm-wiki-docs/<topic>/wiki/` の wiki に残す。1トピック1ページで、自分の言葉で書き、索引とログを付ける。

## Claude での使い方

「これを wiki に入れて」や「これを wiki に保存して」と言う。メッセージがこのスキルを求めているときは、`skill-match` がスキルの名前を挙げる。残す価値のある調査や分析のあとにも、Claude はこのスキルを使う。

## 何をするか

1. 出典は `raw/` にそのまま置く。wiki ページは新しく書いた文章であり、出典を編集したものではない。
2. 1トピックは1ページ。同じトピックなら、よく似た新しいページを作らずに既存のページを更新する。
3. `index.md` は1ページにつき1行を持ち、最初に検索される。
4. `log.md` は追記専用である: `## [YYYY-MM-DD] ingest | title`。
5. ページ同士は `[[page]]` でリンクし、すべての主張は出典を指す。

コードが変われば変わるものはプロジェクト自身のドキュメントに置き、変わらず正しいものは wiki に置く。

## ファイルとスクリプト

```text
~/llm-wiki-docs/<topic>/
  README.md      what the topic holds and where things go
  raw/           sources, untouched
  wiki/          pages, index.md, log.md
```

| スクリプト | すること |
| --- | --- |
| `new-topic.sh <topic> ["description"]` | フォルダと空の索引・ログを作る。既存のものは上書きしない |
| `index-add.py <topic> <page> <category> ["summary"]` | ページを索引に追加する |
| `log-append.py <topic> ingest\|query\|lint "title" [--pages --source --note]` | ログに1件追記する |
| `lint.py [topic]` | 索引やログに載っていないページ、壊れたリンク、孤立したページを見つける |

`LLM_WIKI_ROOT` を使うと、ルートを `~/llm-wiki-docs` 以外の場所に移せる。

## このスキルを支えるフック

`wiki-index-check` は索引に載っていないページを指摘し、`wiki-graph` はグラフを描き直し、`prose-check` は読みにくい箇所を指摘し、`wiki-sync` は回答が終わるときにシェルから編集されたページを拾う。

## 制限

wiki はあなたのマシンにしか存在しない。ほかの場所へ同期する仕組みはない。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
