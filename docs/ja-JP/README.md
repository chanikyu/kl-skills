<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — Claude Code 用のスキルとフックゲートを、まとめてインストールする。2 行のインストールコマンドと、再起動後に表示されるバナー。" width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />
<a href="../wiki/Home-ja.md"><img src="https://img.shields.io/badge/docs-wiki-2F6FEB" alt="ドキュメント wiki" /></a>

[English](../../README.md) · [한국어](../ko-KR/README.md) · **日本語** · [简体中文](../zh-CN/README.md) · [Español](../es/README.md)

[インストール](#インストール) · [スキル](#スキル) · [フックゲート](#フックゲート) · [wiki](../wiki/Home-ja.md)

</div>

<br />

## ひと目で

Claude Code は会話が終わると学んだことを忘れ、長い会話では「わかりやすく書いて」のようなルールから離れていく。

kl-skills は Claude が学んだことを wiki に残し、後の会話で呼び戻す。守るべきルールはフックに入れ、毎ターン検査する。

<img src="../../assets/turn-flow.png" alt="1 ターン: セッション開始、メッセージ受信、ファイル書き込み、Bash 実行、回答終了。それぞれの瞬間にフックゲートが動く。" width="100%" />

| 含まれるもの | 数 | 内容 |
| --- | --: | --- |
| スキル | 10 | wiki、平易な回答、コードのルール、チェックリスト、企画、デバッグ、文献調査 |
| フックゲート | 12 | スキルの案内、チェックリスト、回答の検査、wiki の手入れ、文章とコードの検査 |

<br />

## インストール

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

セッションを再起動すると、最初の行にこう表示される。

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

> [!IMPORTANT]
> ゲートの大半は Python で書かれている。`python3` がないと、それらは黙ってスキップされる。

> [!NOTE]
> ゲートのメッセージと文章のルールは韓国語が基準。日本語の文章は、定義のない略語と長すぎる文だけが検査される。

必要なもの、更新、アンインストール: [インストール](../wiki/Installation-ja.md)。

<br />

## スキル

<img src="../../assets/parts.png" alt="メッセージは Claude Code に届き、Claude Code はスキルを読み、フックゲートの検査を受け、学んだことを wiki に残す。" width="100%" />

名前を押すと、そのスキルの wiki ページが開く。いつ使われるか、何と言えばよいか、何をするかが書いてある。

| スキル | 内容 |
| --- | --- |
| [`llm-wiki-docs`](../wiki/llm-wiki-docs-ja.md) | 学んだことを 1 トピック 1 ページで wiki に残す |
| [`wiki-recall`](../wiki/wiki-recall-ja.md) | 関連する wiki ページを探して回答に使う |
| [`graph-doc-memory`](../wiki/graph-doc-memory-ja.md) | wiki 全体をブラウザでグラフとして描く |
| [`research-to-wiki`](../wiki/research-to-wiki-ja.md) | 調査を、出典ごとの研究の種類とどこまで読んだかを付けて記録する |
| [`natural-answering`](../wiki/natural-answering-ja.md) | 用語、比較基準、結論への一歩を省かずに書く |
| [`readable-code`](../wiki/readable-code-ja.md) | 名前は中身を表し、コメントは理由を表す |
| [`no-hardcoding`](../wiki/no-hardcoding-ja.md) | リスト、パス、しきい値をコードに書き込まない |
| [`task-checklist`](../wiki/task-checklist-ja.md) | すべての指示をチェックリストにし、全項目が終わったときだけ完了する |
| [`planner`](../wiki/planner-ja.md) | 分野と期間に沿って計画し、計画から外れた作業を指摘する |
| [`pipeline-debug`](../wiki/pipeline-debug-ja.md) | 失敗した行ではなく、最初に誤った段階を見つける |

スキルは、会話が説明に合うと Claude が判断したときに読み込まれる。必ず読み込まれる保証はない。`skill-match` ゲートがメッセージごとに合うスキルの名前を挙げ、名前を自分で言ってもよい。

<br />

## フックゲート

| いつ | ゲート | 内容 |
| --- | --- | --- |
| セッション開始 | `session-start` | バナーを表示する |
| メッセージを受け取ったとき | `wiki-recall` | 関連する wiki ページを添える |
| メッセージを受け取ったとき | `skill-match` | このメッセージに合うスキルの名前を挙げる |
| メッセージを受け取ったとき | `checklist-start` | この指示のチェックリストをどこに書くかを伝える |
| ファイルを書いたとき | `wiki-index-check` | 目次にない wiki ページを知らせる |
| ファイルを書いたとき | `wiki-graph` | wiki のグラフを描き直す |
| ファイルを書いたとき | `prose-check` | wiki ページの読みにくい箇所を知らせる |
| ファイルを書いたとき | `code-check` | あいまいな Python の名前と抜けた docstring を知らせる |
| ファイルを書いたとき | `plan-drift` | 計画書の枠組みと逸脱を確認する |
| Bash を実行したとき | `after-bash` | シェルでの wiki の編集とコミットを捉える |
| 回答が終わったとき | `wiki-sync` | どう編集されても、グラフを最新にする |
| 回答が終わったとき | `answer-check` | 回答を検査し、必要なら 1 回だけ差し戻す |
| 回答が終わったとき | `checklist-check` | チェックリストに未完了の項目があれば 1 回だけ差し戻す |

ゲートが回答を差し戻すと、Claude Code に `Stop hook feedback:` と理由が表示される。詳しくは [仕組み](../wiki/How-it-works-ja.md)。

<br />

## 新着

- **0.23** — 分野の用語: 回答とスライドで分野が使わない言葉を `answer-check` が指摘する（`data/domain-terms.tsv`）
- **0.22** — `task-checklist` とその 2 つのゲート、`skill-match`、そしてこのドキュメント wiki
- **0.21** — メンテナー用スキル（`plugin-release`、`hook-replay`）をプラグインから外した。README を 5 言語に
- **0.20** — ファイルを変更したターンは 6 段階の作業報告で終える
- **0.19** — `hook-replay`、`plugin-release`、`research-to-wiki`
- **0.18** — 本当に聞き直されたときだけ止める。計画からの逸脱と wiki の自動検索

全履歴: `git log`。

<br />

## セキュリティ

- ゲートとスキルスクリプトはネットワークを使わない。
- wiki、そのグラフ、計画書、チェックリストはあなたのマシンから出ない。
- 判断できないとき、ゲートはそのターンを通す。

## 開発

リリース、実際の会話でのフック確認、フック出力の約束事、ファイル構成: [docs/DEVELOPMENT.md](../DEVELOPMENT.md)（英語）。

## ライセンス

[MIT](../../LICENSE)
