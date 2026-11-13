**English** · [한국어](readable-code-ko.md) · [日本語](readable-code-ja.md) · [中文](readable-code-zh.md) · [Español](readable-code-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# readable-code

Code the next reader can follow: names that say what they hold, comments that say why.

## Use it in Claude

Nothing to say: it applies whenever code is written or changed.

## What it does

1. A name says what the value is — `student_name`, not `n`.
2. Comments explain why the code is the way it is, not what each line does.
3. Values belong in data files, not in code (see [no-hardcoding](no-hardcoding.md)).

## Files and scripts

| Script | Does |
| --- | --- |
| `check_code.py <files>` | Flags vague names, missing docstrings and long functions with no comment |

Allowed short names and vague names are data files in `data/`.

## Hooks that back it

`code-check` runs on every Python file that is written. It reports and never blocks.

## Limits

The check reads Python only.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
