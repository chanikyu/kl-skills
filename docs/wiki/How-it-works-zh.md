[English](How-it-works.md) · [한국어](How-it-works-ko.md) · [日本語](How-it-works-ja.md) · **中文** · [Español](How-it-works-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# 工作原理

<img src="../../assets/turn-flow.png" alt="一个回合：会话开始，收到一条消息，写入文件，运行 Bash，回答结束。每个时刻都会运行各自的钩子检查。" width="100%" />

## 技能、钩子检查和 wiki

<img src="../../assets/parts.png" alt="你的消息交给 Claude Code，它读取技能，接受钩子检查，并把学到的东西保存在 wiki 里。" width="100%" />

- **技能**说明一项工作该怎么做。当对话与某个技能的描述相符时，Claude Code 会加载这个技能。
  是否相符由模型自己判断，所以并不保证。
- **钩子检查**在固定的时刻运行，不管有没有人记得它们。`skill-match` 填补了上面的空缺：
  它把每条消息与每个技能的触发词逐一比对，并指出适合的技能。
  触发词只有英文和韩文；用其他语言时，由 Claude 自己去比对技能的说明。
- **wiki** 保存学到的东西，一个主题一页，`wiki-recall` 再把它们取回来。

## 钩子检查

| 时机 | 钩子检查 | 作用 | 退回回答 |
| --- | --- | --- | --- |
| 会话开始 | `session-start` | 打印横幅 | — |
| 收到一条消息 | `wiki-recall` | 附上相关的 wiki 页面 | — |
| 收到一条消息 | `skill-match` | 指出这条消息该用哪个技能 | — |
| 收到一条消息 | `checklist-start` | 说明这条指令的清单写在哪里 | — |
| 写入文件 | `wiki-index-check` | 标出没有列入索引的 wiki 页面 | — |
| 写入文件 | `wiki-graph` | 重新绘制 wiki 图 | — |
| 写入文件 | `prose-check` | 标出 wiki 页面中难读的地方 | — |
| 写入文件 | `code-check` | 标出含糊的 Python 命名和缺失的 docstring | — |
| 写入文件 | `plan-drift` | 检查计划的框架和偏离 | — |
| 运行 Bash | `after-bash` | 捕捉在 shell 中进行的 wiki 编辑和提交 | — |
| 回答结束 | `wiki-sync` | 不论页面是怎么编辑的，都把图更新到最新 | — |
| 回答结束 | `answer-check` | 检查回答：用户的重复追问、工作报告、长度、行文 | 一次 |
| 回答结束 | `checklist-check` | 检查清单的每一项是否都已完成 | 一次 |

## 回答被退回时

有两个钩子检查可以在回答到达你之前把它退回给 Claude：`answer-check` 和 `checklist-check`。
这时 Claude Code 会显示 `Stop hook feedback:` 及原因，Claude 会修改回答，或把未完成的项做完。
每个钩子检查**每个回合只这样做一次**；第二次尝试时它只报告还剩下什么，所以一个回合永远不会陷入循环。

## 钩子检查无法判断时

它会让这个回合通过。一个崩溃的钩子检查会破坏它所在事件触发的每一个会话，所以每个钩子检查
遇到看不懂的输入时都会干净地退出。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
