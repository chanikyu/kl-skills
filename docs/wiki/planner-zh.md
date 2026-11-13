[English](planner.md) · [한국어](planner-ko.md) · [日本語](planner-ja.md) · **中文** · [Español](planner-es.md)

[首页](Home-zh.md) · [安装](Installation-zh.md) · [工作原理](How-it-works-zh.md)

# planner

按项目所属领域的做法来做计划，让长期、中期和短期目标保持相连，并标出偏离计划的工作。

## 在 Claude 中使用

说“用 planner 来规划这个”或“为 X 写一份路线图”。对于规划请求，`skill-match` 会指出这个技能。

## 它做什么

1. 先定框架：哪个领域（商业战略、服务与网站、UI/UX、产品、内容、软件、广告、生产与质量）、哪个时间跨度、哪个层级。
2. 然后按顺序推进：调研问题、设定目标、检验可行性、定义功能、撰写需求和规格说明、设计流程和线框图，并与相关团队（由子代理扮演）确定日程。
3. 目标按 `L1` → `M1.2` → `S1.2.3` 编号，这样没有上级目标的任务会被机械地发现。
4. 工作按 `- [YYYY-MM-DD] S1.1.1 …` 的格式记录；计划之外的工作标上 `(계획 밖)`（“计划外”）和原因，完成的目标标上 `완료` 或 `done`（完成）。偏离检查只认一字不差的 `(계획 밖)`。

## 文件和脚本

| 脚本 | 作用 |
| --- | --- |
| `check_plan.py <plan.md>` | 标出缺失的章节、没有上级目标或没有指标的目标，以及没有对应目标的功能 |
| `check_drift.py <plan.md>` | 标出没有声明的计划外工作、逾期的目标，以及没人碰过的长期目标 |

计划模板是 `assets/plan-template.md`；领域指南是 `references/domains.md`。

## 背后的钩子检查

`plan-drift` 在计划被写入时检查它，`after-bash` 在每次提交后检查偏离。两者都只报告，从不阻止。

## 局限

偏离是根据进度日志和提交信息来判断的；不留痕迹的工作看不到。

---

[kl-skills](../../README.md) · MIT 许可证 · 为 [Claude Code](https://claude.com/claude-code) 打造
