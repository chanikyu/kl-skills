**English** · [한국어](natural-answering-ko.md) · [日本語](natural-answering-ja.md) · [中文](natural-answering-zh.md) · [Español](natural-answering-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# natural-answering

Writes answers, reports and documents a reader can follow on the first pass, by refusing to skip the links in the explanation.

## Use it in Claude

Nothing to say: the `answer-check` gate reads every answer.

## What it does

1. Eight things are never skipped: a term's meaning where it first appears, the step from a number to the conclusion, what a number is compared with, why the work was done, the subject of the sentence, units in everyday words, the items behind a count, and plain words for what a reviewer or tool said.
2. The first sentence answers the question that was asked.
3. An answer fits on one screen; anything longer becomes a document with a short summary.
4. After code changes, a report follows six steps: result, summary, changes, verification, problems and limits, follow-up.
5. Terms stay the field's own: the word used in guidelines, papers and your own slides, with a plain meaning in brackets — never a coined substitute.

## Files and scripts

| Script | Does |
| --- | --- |
| `check_prose.py <files>` | Flags undefined terms and acronyms, long sentences and other omissions |
| `check_terms.py <files>` | Finds words the field does not use (pairs in `data/domain-terms.tsv`), also inside .pptx and .docx |

The rules are data in `data/`; the work report and document skeletons are in `references/`.

## Hooks that back it

`answer-check` sends an answer back once when it misses: a question asked again, a turn that changed files without the six-step report, an answer past one screen, or prose findings. `prose-check` reads wiki pages.

It also sends an answer back once when the answer, a file written this turn or a deck the answer points to uses a word listed as wrong in `data/domain-terms.tsv`, and names the field's word. Add a line there whenever you correct a term.

## Limits

The checks are Korean-first. Text in any other language is checked for undefined acronyms and long sentences only.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
