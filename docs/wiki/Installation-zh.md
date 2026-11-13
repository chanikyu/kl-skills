[English](Installation.md) · [한국어](Installation-ko.md) · [日本語](Installation-ja.md) · **中文** · [Español](Installation-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# 安装

## 前提条件

| 需要 | 用途 | 没有它会怎样 |
| --- | --- | --- |
| Claude Code | 安装插件并运行钩子 | 什么都装不上 |
| `python3` | 大多数钩子检查和所有技能脚本（只用标准库） | 这些钩子检查会静默跳过 |
| `git` | 计划偏离检查 | 跳过这项检查 |

预编译的钩子检查支持 macOS（Apple 芯片和 Intel）、Linux（x86_64 和 ARM，也包括 WSL）以及 Windows
（x86_64）。在其他平台上，钩子检查会静默放行。

## 安装

在 Claude Code 中：

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

第一行把这个仓库添加为插件市场；第二行安装插件。

## 确认安装成功

钩子在会话开始时加载，所以请重启 Claude Code。新会话的第一行应该是：

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

看不到这行横幅，说明钩子没有在运行。打开 `/plugin`，确认 kl-skills 已启用。

## 更新

```sh
claude plugin marketplace update kl-skills
claude plugin update kl-skills@kl-skills
```

然后重启会话。

## 卸载

```sh
claude plugin uninstall kl-skills@kl-skills
```

会保留下来的：`~/llm-wiki-docs/` 里的 wiki 及其图、你的计划，以及 `~/.claude/checklists/` 里的清单。
它们属于你，而不属于插件。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
