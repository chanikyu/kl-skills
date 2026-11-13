<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — 为 Claude Code 一次装好技能和钩子检查。两行安装命令，以及重启后出现的横幅。" width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />
<a href="../wiki/Home-zh.md"><img src="https://img.shields.io/badge/docs-wiki-2F6FEB" alt="文档 wiki" /></a>

[English](../../README.md) · [한국어](../ko-KR/README.md) · [日本語](../ja-JP/README.md) · **简体中文** · [Español](../es/README.md)

[安装](#安装) · [技能](#技能) · [钩子检查](#钩子检查) · [wiki](../wiki/Home-zh.md)

</div>

<br />

## 一览

Claude Code 在对话结束后会忘记学到的东西，在长对话里也会渐渐偏离“写得通俗些”这样的规则。

kl-skills 把 Claude 学到的东西记在 wiki 里，并在之后的对话中调出来。要遵守的规则放进钩子，每一轮都会检查。

<img src="../../assets/turn-flow.png" alt="一轮对话：会话开始、收到消息、写入文件、运行 Bash、回答结束。每个时刻都会运行对应的钩子检查。" width="100%" />

| 包含 | 数量 | 作用 |
| --- | --: | --- |
| 技能 | 10 | wiki、通俗回答、代码规则、清单、规划、调试、文献调研 |
| 钩子检查 | 12 | 技能提示、清单、回答检查、wiki 维护、文字与代码检查 |

<br />

## 安装

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

重启会话后，第一行应显示：

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

> [!IMPORTANT]
> 大多数检查用 Python 编写。没有 `python3` 时，它们会静默跳过。

> [!NOTE]
> 检查的提示信息和写作规则以韩语为准。中文文本只检查未定义的缩写和过长的句子。

环境要求、更新和卸载：[安装](../wiki/Installation-zh.md)。

<br />

## 技能

<img src="../../assets/parts.png" alt="你的消息发给 Claude Code，Claude Code 读取技能、接受钩子检查，并把学到的东西记进 wiki。" width="100%" />

点击名字会打开该技能的 wiki 页面：什么时候用、怎么说、它做什么。

| 技能 | 作用 |
| --- | --- |
| [`llm-wiki-docs`](../wiki/llm-wiki-docs-zh.md) | 把学到的东西存进 wiki，一个主题一页 |
| [`wiki-recall`](../wiki/wiki-recall-zh.md) | 找到相关的 wiki 页面并用在回答里 |
| [`graph-doc-memory`](../wiki/graph-doc-memory-zh.md) | 把整个 wiki 画成浏览器里的图 |
| [`research-to-wiki`](../wiki/research-to-wiki-zh.md) | 记录调研结果，并注明每个来源的研究类型和读了多少 |
| [`natural-answering`](../wiki/natural-answering-zh.md) | 写作时不跳过术语、比较基准，也不跳过通向结论的那一步 |
| [`readable-code`](../wiki/readable-code-zh.md) | 名字说明它装的是什么；注释说明为什么 |
| [`no-hardcoding`](../wiki/no-hardcoding-zh.md) | 不让列表、路径和阈值写死在代码里 |
| [`task-checklist`](../wiki/task-checklist-zh.md) | 把每条指令变成清单，只有每一项都完成才结束 |
| [`planner`](../wiki/planner-zh.md) | 按领域和时间跨度做计划，并标出偏离计划的工作 |
| [`pipeline-debug`](../wiki/pipeline-debug-zh.md) | 找出第一个出错的阶段，而不是报错的那一行 |

技能在 Claude 判断对话与其描述相符时才会加载，并不保证每次都加载。`skill-match` 检查会在每条消息上指出合适的技能，你也可以直接说出技能名。

<br />

## 钩子检查

| 时刻 | 检查 | 作用 |
| --- | --- | --- |
| 会话开始 | `session-start` | 显示横幅 |
| 收到消息时 | `wiki-recall` | 附上相关的 wiki 页面 |
| 收到消息时 | `skill-match` | 指出这条消息该用哪个技能 |
| 收到消息时 | `checklist-start` | 说明这条指令的清单写在哪里 |
| 写入文件时 | `wiki-index-check` | 提示不在目录里的 wiki 页面 |
| 写入文件时 | `wiki-graph` | 重绘 wiki 图谱 |
| 写入文件时 | `prose-check` | 提示 wiki 页面中难读的地方 |
| 写入文件时 | `code-check` | 提示含糊的 Python 命名和缺失的 docstring |
| 写入文件时 | `plan-drift` | 检查计划书的框架和偏离 |
| 运行 Bash 时 | `after-bash` | 捕捉在 shell 中对 wiki 的修改和提交 |
| 回答结束时 | `wiki-sync` | 无论页面怎样修改，都让图谱保持最新 |
| 回答结束时 | `answer-check` | 检查回答，必要时退回一次 |
| 回答结束时 | `checklist-check` | 清单里还有未完成的项时退回一次 |

检查退回回答时，Claude Code 会显示 `Stop hook feedback:` 和原因。详见 [工作原理](../wiki/How-it-works-zh.md)。

<br />

## 更新记录

- **0.22** — `task-checklist` 及其两个检查、`skill-match`，以及这个文档 wiki
- **0.21** — 维护者用的技能（`plugin-release`、`hook-replay`）移出插件；README 支持五种语言
- **0.20** — 修改过文件的一轮对话，必须以六步工作报告结束
- **0.19** — `hook-replay`、`plugin-release` 和 `research-to-wiki`
- **0.18** — 只在你真的重复提问时才拦截；计划偏离提示和 wiki 自动检索

完整记录：`git log`。

<br />

## 安全

- 检查和技能脚本不使用网络。
- wiki、图谱、计划书和清单都留在你的电脑上。
- 检查拿不准时，会放行这一轮。

## 开发

发布、用真实对话检查钩子、钩子输出约定和文件结构：[docs/DEVELOPMENT.md](../DEVELOPMENT.md)（英文）。

## 许可证

[MIT](../../LICENSE)
