[English](no-hardcoding.md) · [한국어](no-hardcoding-ko.md) · **日本語** · [中文](no-hardcoding-zh.md) · [Español](no-hardcoding-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# no-hardcoding

値、リスト、対応表、パス、しきい値をコードに書き込まない。

## Claude での使い方

何も言わなくてよい。コードに値を書き込もうとするたびに適用される。

## 何をするか

1. すでにファイルにある値は、そのファイルから読む。コードに書き写すことはしない。
2. 対応表、別名リスト、対象リストはデータファイル（`.tsv`、`.json`）に置く。
3. パスはスクリプトの場所から計算するか、引数で受け取るか、環境変数から読む。
4. しきい値、シード、回数はコマンドライン引数にする。
5. コードに残すのは決して変わらない定数だけで、名前と出典を付ける。

## 制限

モデルが従うためのルールであり、直接チェックするスクリプトはない。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
