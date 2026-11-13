**English** · [한국어](planner-ko.md) · [日本語](planner-ja.md) · [中文](planner-zh.md) · [Español](planner-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# planner

Plans a project the way its field plans, keeps long-, mid- and short-term goals connected, and flags work that drifts from the plan.

## Use it in Claude

Say "Plan this with the planner" or "Write a roadmap for X". `skill-match` names the skill for planning requests.

## What it does

1. Fix the frame first: which field (business strategy, service and web, UI/UX, product, content, software, advertising, production and quality), which horizon, which level.
2. Then work in order: research the problem, set goals, test feasibility, define features, write requirements and specs, design flows and wireframes, and set the schedule with related teams (played by subagents).
3. Goals are numbered `L1` → `M1.2` → `S1.2.3`, so a task with no parent shows up mechanically.
4. Work is logged as `- [YYYY-MM-DD] S1.1.1 …`; work outside the plan carries `(계획 밖)` ("off-plan") and the reason, and a finished goal carries `완료` or `done`. The drift check looks for `(계획 밖)` exactly.

## Files and scripts

| Script | Does |
| --- | --- |
| `check_plan.py <plan.md>` | Flags missing sections, goals without a parent or a target, features without a goal |
| `check_drift.py <plan.md>` | Flags silent off-plan work, overdue goals and long-term goals nobody touched |

The plan template is `assets/plan-template.md`; the field guide is `references/domains.md`.

## Hooks that back it

`plan-drift` checks a plan when it is written, and `after-bash` checks drift after each commit. Both report and never block.

## Limits

Drift is judged from the progress log and commit messages; work that leaves no trace is not seen.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
