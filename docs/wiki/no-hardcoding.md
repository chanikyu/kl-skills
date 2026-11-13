**English** · [한국어](no-hardcoding-ko.md) · [日本語](no-hardcoding-ja.md) · [中文](no-hardcoding-zh.md) · [Español](no-hardcoding-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# no-hardcoding

Keeps values, lists, mappings, paths and thresholds out of the code.

## Use it in Claude

Nothing to say: it applies whenever code is about to carry a value.

## What it does

1. A value that already lives in a file is read from that file, never copied into code.
2. Mapping tables, alias lists and target lists go into data files (`.tsv`, `.json`).
3. Paths are computed from the script's location, taken as arguments, or read from the environment.
4. Thresholds, seeds and counts are command-line arguments.
5. Only constants that never change stay in code, with a name and a source.

## Limits

It is a rule for the model to follow; no script checks it directly.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
