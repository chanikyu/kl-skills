[English](task-checklist.md) · [한국어](task-checklist-ko.md) · **日本語** · [中文](task-checklist-zh.md) · [Español](task-checklist-es.md)

[ホーム](Home-ja.md) · [インストール](Installation-ja.md) · [仕組み](How-it-works-ja.md)

# task-checklist

作業の前にすべての指示をチェックリストにし、全項目が終わるか、理由を付けて閉じられたときだけ完了する。

## Claude での使い方

何も言わなくてよい。`checklist-start` ゲートがメッセージごとにチェックリストを求める。

## 何をするか

1. メッセージ全体を読む。番号付きの項目、文の中に埋もれた依頼、あなたがすでに下した決定まで含める。二通りに読めるときは一方を選んで始めず、最初の項目に `- [ ] 質問: A か B か` と書いて先に尋ねる。
2. それを確かめられる項目に分ける — 「テストを改善する」ではなく「テストが通る」。各項目の末尾に `→ 確認: …` と、何で終わったと判断するかを書く。メッセージ内の質問も1つの項目である。
3. それらをセッションのチェックリストに1行1項目で書く: `- [ ] item`。
4. 終わった項目はすぐに `- [x]` にする。できない項目は `- [~] item — reason` として閉じる。
5. 終える前にリストをもう一度開き、まだ `- [ ]` のものを終わらせる。

## ファイルとスクリプト

```text
~/.claude/checklists/<session>.md         this instruction's list, open items carried over on top
~/.claude/checklists/<session>.prev.md    the previous instruction's whole list, kept
~/.claude/checklists/<session>.carry.md   the open items that were carried over
```

`KL_CHECKLIST_DIR` でフォルダを移せる。

## このスキルを支えるフック

`checklist-start` は前のリストを `.prev.md` として残し、未完了の項目を新しいリストの先頭に引き継いでから、新しい項目をどこに足すかを伝える。`checklist-check` は、リストがないか、未完了の項目があるか、引き継いだ項目が閉じられないまま消えていると、回答を1回差し戻す。

## 制限

ゲートが見るのは項目に印が付いているかどうかであり、印の裏にある作業がきちんと行われたかどうかではない。

---

[kl-skills](../../README.md) · MIT ライセンス · [Claude Code](https://claude.com/claude-code) 向けに作成
