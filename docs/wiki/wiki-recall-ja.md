[English](wiki-recall.md) · [한국어](wiki-recall-ko.md) · **日本語** · [中文](wiki-recall-zh.md) · [Español](wiki-recall-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# wiki-recall

wiki がすでに知っていることを、一から考え直す代わりに回答へ取り込む。

## Claude での使い方

何も言わなくてよい。フックがメッセージごとに wiki を検索する。添えられた行より深く知りたいときは「X について何を決めたっけ？」と聞く。

## 何をするか

1. メッセージごとに、フックは明らかに関連するページのパスと要点の行を添える。条件は、共通する語が2つ以上あり、質問の重みの40%以上をカバーしていることである。関係のないメッセージには何も添えない。
2. さらに深く調べるときは、Claude がページを読む。wiki 全体が小さい（30,000文字以下）ならすべてを読む（CAG）。そうでなければ最も合うページを選ぶ（RAG: BM25、質問のカバー率、グラフ上の隣接ページ）。
3. 韓国語は2文字ずつの断片で照合する。1文字の語は、単独で置かれている場合にだけ数える。

## ファイルとスクリプト

| スクリプト | すること |
| --- | --- |
| `recall.py "question" [--mode auto\|cag\|rag] [--top 3] [--min-coverage 0.4]` | wiki を検索する |

ストップワード、助詞、よく出る断片は `data/` 内のデータファイルにある。`WIKI_RECALL_MIN_COVERAGE` でしきい値を変えられる。

## このスキルを支えるフック

`wiki-recall` ゲートはメッセージごとに動く。

## 制限

添えられる行は、検索で選ばれた抜粋である。引用する前にページを開くこと。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
