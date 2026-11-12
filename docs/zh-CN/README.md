<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — 为 Claude Code 一次装好技能和钩子检查。两行安装命令，以及重启后显示的横幅。" width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />

[English](../../README.md) · [한국어](../ko-KR/README.md) · [日本語](../ja-JP/README.md) · **简体中文** · [Español](../es/README.md)

[安装](#安装) · [开始使用](#开始使用) · [内容](#内容) · [更新记录](#更新记录)

</div>

<br />

## 一览

Claude Code 在对话结束后会忘记学到的东西，在长对话里也会渐渐偏离“写得通俗些”这样的规则。

kl-skills 把 Claude 学到的东西记在 wiki 里，并在之后的对话中调出来。要遵守的规则放进钩子，每次回答都会检查。

<img src="../../assets/turn-flow.png" alt="一轮对话：会话开始、收到消息、写入文件、运行 Bash、回答结束。每个时刻都会运行对应的钩子检查。" width="100%" />

| 包含 | 数量 | 作用 |
| --- | --: | --- |
| 技能 | 9 | wiki、通俗回答、代码规则、规划、调试、文献调研 |
| 钩子检查 | 9 | 回答检查、wiki 维护、文字与代码检查、计划偏离 |

<br />

## 安装

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

重启会话后，第一行应显示：

```
KL-SKILLS GATES v<version> — loaded, 9 rules enforced
```

> [!IMPORTANT]
> 大多数检查用 Python 编写。没有 `python3` 时，它们会静默跳过。

> [!NOTE]
> 检查的提示信息和写作规则以韩语为准。中文文本只检查未定义的缩写和过长的句子。

**更新** — `claude plugin marketplace update kl-skills` → `claude plugin update kl-skills@kl-skills` → 重启。<br />
**卸载** — `claude plugin uninstall kl-skills@kl-skills`。你的 wiki（`~/llm-wiki-docs/`）会保留。

<br />

## 开始使用

从你想做的事开始。对话与技能说明相符时，技能会自动加载；也可以直接点名。

| 你想要 | 这样说 | 技能 |
| --- | --- | --- |
| 记下学到的东西 | “把这个整理到 wiki 里” | `llm-wiki-docs` |
| 用上 wiki 里的知识 | 不用说 — 每条消息都会与 wiki 比对 | `wiki-recall` |
| 查看整个 wiki | “给我看 wiki 图谱” | `graph-doc-memory` |
| 调研一个问题 | “调研一下 X 是否导致 Y” | `research-to-wiki` |
| 规划项目 | “用 planner 规划一下” | `planner` |
| 找出出错原因 | “找出这个错误的原因” | `pipeline-debug` |
| 写代码 | 不用说 — 命名、注释和禁止硬编码的规则会生效 | `readable-code` · `no-hardcoding` |

检查拦下回答时，Claude Code 会显示 `Stop hook feedback:` 和原因，Claude 会重写回答。只有 `answer-check` 会拦截，而且每轮只拦一次。

<br />

## 内容

<img src="../../assets/parts.png" alt="你的消息交给 Claude Code，它读取技能、接受钩子检查，并把学到的东西记进 wiki。" width="100%" />

### 技能

| 技能 | 作用 |
| --- | --- |
| `llm-wiki-docs` | 把学到的东西记进 wiki，一个主题一页 |
| `wiki-recall` | 找到相关的 wiki 页面并用在回答里 |
| `graph-doc-memory` | 把整个 wiki 画成图谱，在浏览器中显示 |
| `research-to-wiki` | 记录调研结果，并标明每个来源的研究类型和读了多少 |
| `natural-answering` | 写作时不省略术语、比较基准和得出结论的中间步骤 |
| `readable-code` | 名字说明装的是什么，注释说明为什么 |
| `no-hardcoding` | 不把列表、路径和阈值写死在代码里 |
| `pipeline-debug` | 找出最先出错的环节，而不是报错的那一行 |
| `planner` | 按领域和周期做规划，并提示偏离计划的工作 |

### 钩子检查

| 时机 | 检查 | 作用 |
| --- | --- | --- |
| 会话开始 | `session-start` | 显示横幅 |
| 收到消息时 | `wiki-recall` | 附上相关的 wiki 页面 |
| 写入文件时 | `wiki-index-check` | 提示不在目录里的 wiki 页面 |
| 写入文件时 | `wiki-graph` | 重绘 wiki 图谱 |
| 写入文件时 | `prose-check` | 提示 wiki 页面中难读的地方 |
| 写入文件时 | `code-check` | 提示含糊的 Python 命名和缺失的 docstring |
| 写入文件时 | `plan-drift` | 检查计划书的框架和偏离 |
| 运行 Bash 时 | `after-bash` | 捕捉在 shell 中对 wiki 的修改和提交 |
| 回答结束时 | `wiki-sync` | 无论页面怎样修改，都让图谱保持最新 |
| 回答结束时 | `answer-check` | 检查回答，必要时拦截一次 |

<br />

## 更新记录

0.17–0.20 于 2026-11-11 发布，0.21 于 2026-11-12 发布。完整历史见 `git log`。

- **0.21** — 维护者用的技能（`plugin-release`、`hook-replay`）移出插件；README 支持五种语言
- **0.20** — 修改过文件的一轮对话，必须以六步工作报告结束
- **0.19** — `hook-replay`、`plugin-release` 和 `research-to-wiki`
- **0.18** — 只在你真的重复提问时才拦截；计划偏离提示和 wiki 自动检索
- **0.17** — `planner`

<br />

## 环境要求

| 需要 | 用途 | 没有时 |
| --- | --- | --- |
| `python3` | 大多数检查和所有技能脚本（仅用标准库） | 这些检查会静默跳过 |
| `git` | 计划偏离检查 | 跳过该检查 |

预编译的检查程序支持 macOS（Apple 芯片与 Intel）、Linux（x86_64 与 ARM，含 WSL）和 Windows（x86_64）。其他环境下，检查会静默放行。

<br />

## 安全

- 检查和技能脚本不使用网络。
- wiki、图谱和计划书都留在你的电脑上。
- 检查拿不准时，会放行这一轮。

<br />

## 开发

发布、用真实对话检查钩子、钩子输出约定和文件结构：[docs/DEVELOPMENT.md](../DEVELOPMENT.md)（英文）。

## 许可证

MIT
