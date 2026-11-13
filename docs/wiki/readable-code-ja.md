[English](readable-code.md) · [한국어](readable-code-ko.md) · **日本語** · [中文](readable-code-zh.md) · [Español](readable-code-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# readable-code

次に読む人が追えるコードにする。名前は中身を表し、コメントは理由を表す。

## Claude での使い方

何も言わなくてよい。コードを書いたり変更したりするたびに適用される。

## 何をするか

1. 名前は値が何であるかを表す — `n` ではなく `student_name`。
2. コメントは、各行が何をするかではなく、コードがなぜそうなっているかを説明する。
3. 値はコードではなくデータファイルに置く（[no-hardcoding](no-hardcoding-ja.md) を参照）。

## ファイルとスクリプト

| スクリプト | すること |
| --- | --- |
| `check_code.py <files>` | あいまいな名前、docstring の欠落、コメントのない長い関数を指摘する |

許可される短い名前とあいまいな名前は、`data/` 内のデータファイルにある。

## このスキルを支えるフック

`code-check` は書かれたすべての Python ファイルに対して動く。報告するだけで、止めることはない。

## 制限

チェックが読むのは Python だけである。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
