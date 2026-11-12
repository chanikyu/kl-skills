<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — Claude Code 用のスキルとフックゲートをまとめてインストールする。インストールコマンド 2 行と、再起動後に表示されるバナー。" width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />

[English](../../README.md) · [한국어](../ko-KR/README.md) · **日本語** · [简体中文](../zh-CN/README.md) · [Español](../es/README.md)

[インストール](#インストール) · [はじめに](#はじめに) · [中身](#中身) · [新着](#新着)

</div>

<br />

## ひと目で

Claude Code は会話が終わると学んだことを忘れ、長い会話では「わかりやすく書いて」のようなルールから離れていく。

kl-skills は Claude が学んだことを wiki に残し、後の会話で呼び戻す。守るべきルールはフックに入れ、毎回の回答を検査する。

<img src="../../assets/turn-flow.png" alt="1 ターン: セッション開始、メッセージ受信、ファイル書き込み、Bash 実行、回答終了。それぞれの瞬間にフックゲートが動く。" width="100%" />

| 含まれるもの | 数 | 内容 |
| --- | --: | --- |
| スキル | 9 | wiki、平易な回答、コードのルール、企画、デバッグ、文献調査 |
| フックゲート | 9 | 回答の検査、wiki の手入れ、文章とコードの検査、計画からの逸脱 |

<br />

## インストール

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

セッションを再起動すると、最初の行にこう表示される。

```
KL-SKILLS GATES v<version> — loaded, 9 rules enforced
```

> [!IMPORTANT]
> ゲートの大半は Python で書かれている。`python3` がないと、それらは黙ってスキップされる。

> [!NOTE]
> ゲートのメッセージと文章のルールは韓国語が基準。日本語の文章は、定義のない略語と長すぎる文だけが検査される。

**更新** — `claude plugin marketplace update kl-skills` → `claude plugin update kl-skills@kl-skills` → 再起動。<br />
**アンインストール** — `claude plugin uninstall kl-skills@kl-skills`。wiki（`~/llm-wiki-docs/`）は残る。

<br />

## はじめに

やりたいことから始める。会話がスキルの説明に合うとスキルが読み込まれる。名前で呼んでもよい。

| やりたいこと | こう言う | スキル |
| --- | --- | --- |
| 学んだことを残す | 「wiki にまとめて」 | `llm-wiki-docs` |
| wiki の知識を使う | 何も言わなくてよい — メッセージごとに wiki と照らし合わせる | `wiki-recall` |
| wiki 全体を見る | 「wiki のグラフを見せて」 | `graph-doc-memory` |
| 調べる | 「X が Y の原因か調べて」 | `research-to-wiki` |
| 企画する | 「planner で企画して」 | `planner` |
| 壊れた原因を探す | 「このエラーの原因を探して」 | `pipeline-debug` |
| コードを書く | 何も言わなくてよい — 命名・コメント・ハードコーディング禁止のルールが効く | `readable-code` · `no-hardcoding` |

ゲートが回答を止めると、Claude Code に `Stop hook feedback:` と理由が表示され、Claude が回答を書き直す。止めるゲートは `answer-check` だけで、1 ターンに 1 回だけ止める。

<br />

## 中身

<img src="../../assets/parts.png" alt="メッセージは Claude Code に届き、Claude Code はスキルを読み、フックゲートの検査を受け、学んだことを wiki に残す。" width="100%" />

### スキル

| スキル | 内容 |
| --- | --- |
| `llm-wiki-docs` | 学んだことを、1 トピック 1 ページで wiki にまとめる |
| `wiki-recall` | 関連する wiki ページを探して回答に使う |
| `graph-doc-memory` | wiki 全体をグラフにしてブラウザに表示する |
| `research-to-wiki` | 出典ごとに研究の種類とどこまで読んだかを記録して調査を残す |
| `natural-answering` | 用語、比較の基準、結論までの途中の段階を省かずに書く |
| `readable-code` | 名前は中身を表し、コメントには理由を書く |
| `no-hardcoding` | リスト、パス、しきい値をコードに埋め込まない |
| `pipeline-debug` | エラーが出た行ではなく、最初におかしくなった段階を探す |
| `planner` | 分野と期間に合わせて企画し、計画から外れた作業を知らせる |

### フックゲート

| いつ | ゲート | 内容 |
| --- | --- | --- |
| セッション開始 | `session-start` | バナーを表示する |
| メッセージを受け取ったとき | `wiki-recall` | 関連する wiki ページを添える |
| ファイルを書いたとき | `wiki-index-check` | 目次にない wiki ページを知らせる |
| ファイルを書いたとき | `wiki-graph` | wiki のグラフを描き直す |
| ファイルを書いたとき | `prose-check` | wiki ページの読みにくい箇所を知らせる |
| ファイルを書いたとき | `code-check` | あいまいな Python の名前と抜けた docstring を知らせる |
| ファイルを書いたとき | `plan-drift` | 計画書の枠組みと逸脱を確認する |
| Bash を実行したとき | `after-bash` | シェルでの wiki の編集とコミットを捉える |
| 回答が終わったとき | `wiki-sync` | どう編集されても、グラフを最新にする |
| 回答が終わったとき | `answer-check` | 回答を検査し、必要なら 1 回だけ止める |

<br />

## 新着

0.17〜0.20 は 2026-11-11、0.21 は 2026-11-12 に公開。全履歴は `git log`。

- **0.21** — メンテナー用スキル（`plugin-release`、`hook-replay`）をプラグインから外した。README を 5 言語に
- **0.20** — ファイルを変更したターンは 6 段階の作業報告で終える
- **0.19** — `hook-replay`、`plugin-release`、`research-to-wiki`
- **0.18** — 本当に聞き直されたときだけ止める。計画からの逸脱と wiki の自動検索
- **0.17** — `planner`

<br />

## 必要なもの

| 必要なもの | 用途 | ないと |
| --- | --- | --- |
| `python3` | ゲートの大半とすべてのスキルスクリプト（標準ライブラリのみ） | それらのゲートは黙ってスキップされる |
| `git` | 計画からの逸脱の検査 | その検査はスキップされる |

ビルド済みのゲートは macOS（Apple シリコン・Intel）、Linux（x86_64・ARM、WSL を含む）、Windows（x86_64）向けを同梱している。それ以外の環境では、ゲートは黙って通す。

<br />

## セキュリティ

- ゲートとスキルスクリプトはネットワークを使わない。
- wiki、そのグラフ、計画書はあなたのマシンから出ない。
- 判断できないとき、ゲートはそのターンを通す。

<br />

## 開発

リリース、実際の会話でのフック確認、フック出力の約束事、ファイル構成: [docs/DEVELOPMENT.md](../DEVELOPMENT.md)（英語）。

## ライセンス

MIT
