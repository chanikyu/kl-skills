**English** · [한국어](Installation-ko.md) · [日本語](Installation-ja.md) · [中文](Installation-zh.md) · [Español](Installation-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# Installation

## Requirements

| Needs | For | Without it |
| --- | --- | --- |
| Claude Code | installs the plugin and runs the hooks | nothing installs |
| `python3` | most gates and every skill script (standard library only) | those gates skip quietly |
| `git` | plan drift checks | that check is skipped |

Prebuilt gates ship for macOS (Apple silicon and Intel), Linux (x86_64 and ARM, also WSL) and Windows
(x86_64). On anything else the gates pass silently.

## Install

In Claude Code:

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

The first line adds this repository as a marketplace; the second installs the plugin.

## Check that it worked

Hooks load when a session starts, so restart Claude Code. The first line of the new session should read:

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

No banner means the hooks are not running. Open `/plugin` and check that kl-skills is enabled.

## Update

```sh
claude plugin marketplace update kl-skills
claude plugin update kl-skills@kl-skills
```

Then restart the session.

## Uninstall

```sh
claude plugin uninstall kl-skills@kl-skills
```

What stays: your wiki in `~/llm-wiki-docs/` with its graph, your plans, and the checklists in
`~/.claude/checklists/`. They are yours, not the plugin's.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
