**English** · [한국어](research-to-wiki-ko.md) · [日本語](research-to-wiki-ja.md) · [中文](research-to-wiki-zh.md) · [Español](research-to-wiki-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# research-to-wiki

Turns a research request into a wiki page that shows how far each claim is established.

## Use it in Claude

Say "Research whether X causes Y" or "Look up the evidence for X". `skill-match` names the skill for research requests.

## What it does

1. Search the wiki first; update an existing page instead of starting a new one.
2. Search the literature for both sides of the question and for confounders.
3. End every source line with two labels, `— <study type> · <how much was read>`. The checker reads the Korean names in its data files: study type `메타분석` (meta-analysis), `무작위시험` (randomized trial), `추적관찰` (cohort), `유전분석` (Mendelian randomization), `단면비교` (cross-sectional), `동물실험` (animal), `세포실험` (cell), `리뷰` (review), `의견` (opinion); how much was read `본문` (full text), `초록` (abstract), `검색요약` (search summary).
4. Write the page with the conclusion first, in your own words, numbers next to what they compare with.
5. Check it, then register it in the wiki index and log.

## Files and scripts

| Script | Does |
| --- | --- |
| `check_research.py <page>` | Flags a missing conclusion, sources without a link or labels, and citations without a source |

The label names are data files (`data/evidence-levels.tsv`, `data/reading-levels.txt`); the page template is `assets/research-page-template.md`.

## Limits

The check sees whether the labels are there, not whether they are right. That still takes reading the paper.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
