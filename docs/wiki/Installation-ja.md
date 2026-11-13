[English](Installation.md) · [한국어](Installation-ko.md) · **日本語** · [中文](Installation-zh.md) · [Español](Installation-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# インストール

## 必要なもの

| 必要なもの | 用途 | ないと |
| --- | --- | --- |
| Claude Code | プラグインをインストールし、フックを実行する | 何もインストールされない |
| `python3` | ほとんどのゲートと、すべてのスキルスクリプト（標準ライブラリのみ） | それらのゲートは黙ってスキップされる |
| `git` | 計画からのずれのチェック | そのチェックはスキップされる |

ビルド済みのゲートは macOS（Apple シリコンと Intel）、Linux（x86_64 と ARM、WSL も含む）、Windows（x86_64）向けに同梱されている。それ以外の環境では、ゲートは何もせずに通過する。

## インストール

Claude Code で次を実行する。

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

1行目はこのリポジトリをマーケットプレイスとして追加し、2行目はプラグインをインストールする。

## 動作を確かめる

フックはセッションの開始時に読み込まれるので、Claude Code を再起動する。新しいセッションの最初の行は次のようになるはずである。

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

バナーが出なければ、フックは動いていない。`/plugin` を開き、kl-skills が有効になっているかを確かめる。

## 更新

```sh
claude plugin marketplace update kl-skills
claude plugin update kl-skills@kl-skills
```

その後、セッションを再起動する。

## アンインストール

```sh
claude plugin uninstall kl-skills@kl-skills
```

残るもの: `~/llm-wiki-docs/` にある wiki とそのグラフ、計画、`~/.claude/checklists/` にあるチェックリスト。これらはプラグインのものではなく、あなたのものである。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
