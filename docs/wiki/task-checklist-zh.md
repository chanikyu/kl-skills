[English](task-checklist.md) · [한국어](task-checklist-ko.md) · [日本語](task-checklist-ja.md) · **中文** · [Español](task-checklist-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# task-checklist

在动手之前把每条指令变成清单，只有每一项都已完成、或者带着理由关闭之后才结束。

## 在 Claude 中使用

什么都不用说：`checklist-start` 钩子检查会在每条消息时要求写清单。

## 它做什么

1. 读完整条消息：带编号的条目、埋在句子里的请求、你已经做出的决定。
2. 把它拆成可以核对的条目——写“测试通过”，而不是“改进测试”。消息里的问题也算一项。
3. 把它们写进本会话的清单，每行一项：`- [ ] item`。
4. 每一项一完成就标成 `- [x]`；做不了的项关闭为 `- [~] item — reason`。
5. 结束之前再打开清单，把仍是 `- [ ]` 的项做完。

## 文件和脚本

```text
~/.claude/checklists/<session>.md        this instruction's list
~/.claude/checklists/<session>.prev.md   the previous instruction's list, kept
```

`KL_CHECKLIST_DIR` 可以移动这个文件夹。

## 背后的钩子检查

`checklist-start` 把上一份清单挪到一边，并说明新清单写在哪里。如果清单缺失或还有未完成的项，`checklist-check` 会把回答退回一次。

## 局限

钩子检查只看条目有没有标记，不看标记背后的工作做得好不好。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
