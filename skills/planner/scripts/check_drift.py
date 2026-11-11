#!/usr/bin/env python3
"""실제로 한 일이 중장기 계획을 따라가고 있는지 본다.

    check_drift.py [--days 30] [--no-git] [--latest-commit] PLAN.md

check_plan.py 가 "계획이 제대로 쓰였나" 를 본다면, 이 스크립트는 "일이 계획을 따라가나" 를 본다.
한 일은 두 곳에서 읽는다.

  진행 기록  계획서의 '진행 기록' 절. 한 줄에 하나: - [2026-11-12] S1.1.1 실패 로그 40건 분류
             계획에 없는 일은 '(계획 밖)' 을 붙이고 이유를 쓴다. 끝낸 목표에는 '완료' 를 쓴다
  git 커밋   계획서가 든 저장소의 최근 커밋 메시지. 목표 번호를 쓰면 그 목표의 일로 센다

보고하는 것:

  off-plan-work   목표 번호도 '(계획 밖)' 표시도 없는 일 — 계획에서 조용히 벗어난 일
  unknown-goal    없는 목표 번호를 가리키는 일
  overdue-goal    기준에 적은 날짜가 지났는데 '완료' 가 없는 목표
  drifting        최근 한 일 가운데 계획 안의 비율이 기준보다 낮다
  neglected-long  최근에 한 일이 하나도 없는 장기 목표 — 그 방향에서 멀어지고 있다 (참고)
  stalled-goal    일을 시작한 계획에서 오래 손대지 않은 단기 목표 (참고)

같은 날 같은 목표로 진행 기록과 커밋이 둘 다 있으면 한 건으로 센다. 기록하는 곳이 둘이라고
일이 두 번 된 것은 아니다.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_plan import GOAL_DEFINITION, GOAL_REFERENCE, split_sections  # noqa: E402

PROGRESS_ENTRY = re.compile(r"^\s*[-*]\s*\[(\d{4}-\d{2}-\d{2})\]\s*(.*)$")
DATE_IN_TEXT = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
OFF_PLAN_MARK = "(계획 밖)"          # 계획에 없는 일을 알고 했다는 표시
DONE_WORDS = ("완료", "done", "closes", "끝냄")   # 이 말과 목표 번호가 함께 있으면 그 목표는 끝난 것


def long_term_of(goal_id):
    """어느 장기 목표 아래의 일인가. L1, M1.2, S1.2.3 은 모두 L1 아래다."""
    return "L" + goal_id[1:].split(".")[0]


def read_plan(path):
    """계획서에서 목표 정의와 진행 기록을 읽는다."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    goals = {}
    for lineno, line in enumerate(lines, 1):
        definition = GOAL_DEFINITION.match(line)
        if definition:
            goals[definition.group(1)] = {"line": lineno, "text": definition.group(2)}
    progress = []
    for title, start, body in split_sections(lines):
        if "진행 기록" not in title:
            continue
        for offset, line in enumerate(body, 1):
            entry = PROGRESS_ENTRY.match(line)
            if entry:
                progress.append({"date": entry.group(1), "text": entry.group(2),
                                 "where": "진행 기록 %d행" % (start + offset)})
    return goals, progress


def read_commits(plan_path, days):
    """계획서가 든 저장소의 최근 커밋. 봇이 만든 커밋은 사람의 일이 아니므로 뺀다."""
    folder = os.path.dirname(os.path.abspath(plan_path))
    try:
        finished = subprocess.run(
            ["git", "-C", folder, "log", "--no-merges", "--since=%d days ago" % days,
             "--date=short", "--format=%h%x09%ad%x09%an%x09%s"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []
    commits = []
    for line in (finished.stdout or b"").decode("utf-8", "replace").splitlines():
        parts = line.split("\t", 3)
        if len(parts) < 4 or parts[2].endswith("[bot]"):
            continue
        commits.append({"date": parts[1], "text": parts[3], "where": "커밋 %s" % parts[0]})
    return commits


def analyse(goals, work_items, today, options):
    """한 일들을 목표와 대조해 (등급, 이름, 설명) 목록과 요약 줄을 만든다."""
    found = []
    since = today - datetime.timedelta(days=options.days)
    recent = [item for item in work_items
              if datetime.date.fromisoformat(item["date"]) >= since]

    # 같은 날 같은 목표의 일은 한 건이다 — 진행 기록과 커밋이 같은 일을 두 번 적었을 수 있다.
    seen_keys, counted = set(), []
    for item in recent:
        refs = sorted(set(GOAL_REFERENCE.findall(item["text"])))
        key = (item["date"], tuple(refs)) if refs else (item["date"], item["where"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        counted.append(dict(item, refs=refs))

    on_plan, off_plan, acknowledged = [], [], []
    for item in counted:
        valid = [ref for ref in item["refs"] if ref in goals]
        for ref in item["refs"]:
            if ref not in goals:
                found.append(("warn", "unknown-goal",
                              "%s 가 없는 목표 %s 를 가리킨다" % (item["where"], ref)))
        if valid:
            on_plan.append(dict(item, refs=valid))
        elif OFF_PLAN_MARK in item["text"]:
            acknowledged.append(item)
        else:
            off_plan.append(item)
            found.append(("warn", "off-plan-work",
                          "%s 는 어느 목표의 일인지 없다: %s" % (item["where"], item["text"][:50])))

    # 끝난 목표: 목표 번호와 '완료' 류 말이 한 줄에 함께 있는 일
    done = set()
    for item in work_items:
        if any(word in item["text"] for word in DONE_WORDS):
            done.update(ref for ref in GOAL_REFERENCE.findall(item["text"]) if ref in goals)

    for goal_id, goal in goals.items():
        dates = DATE_IN_TEXT.findall(goal["text"])
        if dates and goal_id not in done and max(dates) < today.isoformat():
            found.append(("warn", "overdue-goal",
                          "%s 의 기한 %s 이 지났는데 완료 기록이 없다" % (goal_id, max(dates))))

    total = len(on_plan) + len(off_plan) + len(acknowledged)
    if total >= options.min_items and len(on_plan) / total < options.min_on_plan:
        found.append(("warn", "drifting",
                      "최근 %d일 한 일 %d건 중 계획 안은 %d건(%d%%) — 기준 %d%% 보다 낮다"
                      % (options.days, total, len(on_plan), 100 * len(on_plan) // total,
                         int(options.min_on_plan * 100))))

    per_long = {goal_id: 0 for goal_id in goals if goal_id.startswith("L")}
    for item in on_plan:
        for long_id in {long_term_of(ref) for ref in item["refs"]}:
            if long_id in per_long:
                per_long[long_id] += 1
    if total >= options.min_items:
        for long_id, count in sorted(per_long.items()):
            if count == 0:
                found.append(("note", "neglected-long",
                              "최근 %d일 동안 %s 아래로 한 일이 없다 — 이 장기 목표에서 멀어지고 있다"
                              % (options.days, long_id)))

    # 손대지 않은 단기 목표는, 일을 시작한 계획에서만 의미가 있다. 막 쓴 계획은 다 손 안 댔다.
    if work_items:
        last_touched = {}
        for item in work_items:
            for ref in GOAL_REFERENCE.findall(item["text"]):
                last_touched[ref] = max(last_touched.get(ref, ""), item["date"])
        stale_line = (today - datetime.timedelta(days=options.stale_days)).isoformat()
        for goal_id in goals:
            if goal_id.startswith("S") and goal_id not in done \
                    and last_touched.get(goal_id, "") < stale_line:
                found.append(("note", "stalled-goal",
                              "%s 를 %d일 넘게 손대지 않았다" % (goal_id, options.stale_days)))

    summary = ["계획 이탈 요약 (최근 %d일, 한 일 %d건)" % (options.days, total)]
    if total:
        summary.append("  계획 안 %d건 (%d%%) · 계획 밖 %d건 · 이유를 밝힌 계획 밖 %d건"
                       % (len(on_plan), 100 * len(on_plan) // total, len(off_plan),
                          len(acknowledged)))
        summary.append("  장기 목표별: " + " · ".join("%s %d건" % pair
                                                   for pair in sorted(per_long.items())))
    return found, summary


def main(argv=None):
    """명령줄 입구. 경고가 있으면 1로 끝낸다."""
    parser = argparse.ArgumentParser(description="한 일이 중장기 계획을 따라가는지 본다.")
    parser.add_argument("plan")
    parser.add_argument("--days", type=int, default=30, help="최근 며칠의 일을 볼지 (기본 30)")
    parser.add_argument("--stale-days", type=int, default=14,
                        help="이 날수 넘게 손 안 댄 단기 목표를 알린다 (기본 14)")
    parser.add_argument("--min-on-plan", type=float, default=0.7,
                        help="계획 안 일의 비율이 이보다 낮으면 이탈로 본다 (기본 0.7)")
    parser.add_argument("--min-items", type=int, default=5,
                        help="비율을 따지려면 일이 최소 몇 건 있어야 하는가 (기본 5)")
    parser.add_argument("--no-git", action="store_true", help="커밋은 보지 않는다")
    parser.add_argument("--latest-commit", action="store_true",
                        help="마지막 커밋 하나에 목표 번호가 있는지도 따로 알린다")
    parser.add_argument("--today", default=None, help="오늘 날짜를 바꾼다 (테스트용, YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="참고 등급까지 보여준다")
    options = parser.parse_args(argv)

    today = datetime.date.fromisoformat(options.today) if options.today else datetime.date.today()
    goals, progress = read_plan(options.plan)
    commits = [] if options.no_git else read_commits(options.plan, options.days)
    found, summary = analyse(goals, progress + commits, today, options)

    # 커밋 직후 훅에서 부를 때는 "방금 한 일" 이 계획 밖인지를 따로, 맨 앞에 알린다.
    # 30일 요약 속에 묻히면 지금 무엇이 문제인지 안 보인다. 지난 일 하나하나는 빼고 요약으로만
    # 남긴다 — 커밋할 때마다 지난 커밋 스물 몇 줄이 다시 나오면 아무도 읽지 않는다.
    if options.latest_commit:
        found = [item for item in found if item[1] != "off-plan-work"]
    if options.latest_commit and commits and not GOAL_REFERENCE.findall(commits[0]["text"]) \
            and OFF_PLAN_MARK not in commits[0]["text"]:
        found.insert(0, ("warn", "off-plan-work",
                         "방금 커밋(%s)이 계획의 어느 목표에도 연결되지 않는다"
                         % commits[0]["where"].split()[-1]))

    shown = [item for item in found if options.all or item[0] == "warn"]
    for severity, code, message in shown:
        print("%s [%s] %s" % (options.plan, code, message))
    print("\n".join(summary))
    warning_count = sum(1 for item in found if item[0] == "warn")
    print("planner: 이탈 경고 %d건" % warning_count)
    return 1 if warning_count else 0


if __name__ == "__main__":
    sys.exit(main())
