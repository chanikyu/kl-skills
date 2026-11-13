**English** · [한국어](pipeline-debug-ko.md) · [日本語](pipeline-debug-ja.md) · [中文](pipeline-debug-zh.md) · [Español](pipeline-debug-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# pipeline-debug

When code fails or gives a wrong result, traces the fault back along the pipeline instead of patching the line where it surfaced.

## Use it in Claude

Say "Find the root cause of this error". `skill-match` names the skill for errors, tracebacks and failed runs.

## What it does

1. Map the stages the data went through.
2. Check what went into and came out of each stage — counts, columns, a few real values — against what was expected.
3. The first stage whose output is wrong is the cause; the error usually appears further down.
4. Reproduce the fault at that stage, pin it with a failing check, fix it there, and run every later stage again.

## Files and scripts

| Script | Does |
| --- | --- |
| `probe.py [--rows N] FILE ...` | Shows rows, columns, blanks and the first lines of a file passed between stages |

## Limits

It needs the intermediate files; a pipeline that keeps nothing between stages has to be run again with them saved.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
