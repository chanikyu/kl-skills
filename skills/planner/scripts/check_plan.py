#!/usr/bin/env python3
"""기획서가 틀을 지켰는지, 목표들이 위아래로 이어지는지 본다.

    check_plan.py [--all] PLAN.md [PLAN.md...]

기획의 내용이 좋은지는 기계가 판단하지 못한다. 하지만 **연결이 끊긴 자리**는 찾을 수 있다.
이 스크립트가 보는 것은 그것뿐이다.

  missing-section    필수 절이 없다 (단계를 건너뛰었다)
  empty-section      절 제목만 있고 내용이 비었거나 틀의 자리표시만 남았다
  no-domain          "0. 틀" 에 분야가 적혀 있지 않다
  orphan-goal        중기 목표의 부모 장기 목표가, 또는 단기 목표의 부모 중기 목표가 없다
  unmeasured-goal    목표에 잴 기준(숫자나 '기준')이 없다
  unlinked-feature   어느 목표를 위한 기능인지 적혀 있지 않다
  unknown-goal       없는 목표 번호를 가리킨다
  childless-goal     장기 목표 아래 중기가, 중기 아래 단기가 하나도 없다 (참고 등급)

목표 번호가 부모를 말한다: M1.2 의 부모는 L1, S1.2.3 의 부모는 M1.2.
"장기에 맞게 중기, 중기에 맞게 단기" 라는 원칙을 기계가 확인할 수 있는 모양으로 바꾼 것이다.

필수 절 목록과 분야 이름은 data/ 의 파일에서 읽는다. 코드에 두지 않는다.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
# 목표 정의는 "- [L1] ..." 처럼 줄 앞의 대괄호 안에 쓴다. 참조는 대괄호 없이 어디서든.
GOAL_DEFINITION = re.compile(r"^\s*[-*]\s*\[(L\d+|M\d+\.\d+|S\d+\.\d+\.\d+)\]\s*(.*)$")
GOAL_REFERENCE = re.compile(r"\b(L\d+|M\d+\.\d+|S\d+\.\d+\.\d+)\b")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# 틀에서 그대로 옮겨 온 자리표시. <...> 만 남은 줄은 내용이 아니다.
PLACEHOLDER = re.compile(r"^[\s\-*]*<[^>]*>[\s.]*$")


def load_lines(filename):
    """데이터 파일 한 장을 줄 목록으로. # 으로 시작하는 줄과 빈 줄은 뺀다."""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, encoding="utf-8") as handle:
            return [line.strip() for line in handle
                    if line.strip() and not line.strip().startswith("#")]
    except OSError:
        return []


def squash(text):
    """가운뎃점·빗금·공백을 지워 비교한다. 경영·전략, 경영/전략, 경영 전략을 같게 본다."""
    return re.sub(r"[\s·/]", "", text)


def split_sections(lines):
    """(제목, 줄번호, 본문 줄 목록) 을 순서대로. 본문은 다음 제목 전까지다."""
    sections = []
    for lineno, line in enumerate(lines, 1):
        heading = HEADING.match(line)
        if heading:
            sections.append([heading.group(2).strip(), lineno, []])
        elif sections:
            sections[-1][2].append(line)
    return sections


def parent_of(goal_id):
    """M1.2 -> L1, S1.2.3 -> M1.2. 장기 목표는 부모가 없다."""
    if goal_id.startswith("M"):
        return "L" + goal_id[1:].split(".")[0]
    if goal_id.startswith("S"):
        return "M" + ".".join(goal_id[1:].split(".")[:2])
    return None


def check(path, text, show_notes):
    """기획서 한 장을 검사해 (줄, 등급, 이름, 설명) 목록을 돌려준다."""
    lines = text.splitlines()
    found = []

    def add(lineno, severity, code, message):
        found.append((lineno, severity, code, message))

    sections = split_sections(lines)

    # 필수 절: 제목에 그 말이 들어 있으면 있는 것으로 본다. 번호(1-1. 등)는 쓰는 사람 마음이다.
    for required in load_lines("required-sections.txt"):
        match = next((section for section in sections if required in section[0]), None)
        if match is None:
            add(1, "warn", "missing-section", "'%s' 절이 없다 — 이 단계를 건너뛰었다" % required)
            continue
        body = [line for line in match[2] if line.strip() and not PLACEHOLDER.match(line)]
        if not body:
            add(match[1], "warn", "empty-section",
                "'%s' 절이 비었거나 틀의 자리표시만 남았다" % required)

    # 분야: "틀" 절에 여덟 분야 중 하나가 적혀 있어야 기획 방향이 정해진 것이다.
    frame = next((section for section in sections if section[0].endswith("틀")), None)
    if frame is not None:
        frame_text = squash(" ".join(line for line in frame[2] if not PLACEHOLDER.match(line)))
        # 자리표시 안에 분야 목록이 통째로 들어 있으면 고른 것이 아니다.
        frame_text = re.sub(r"<[^>]*>", "", frame_text)
        if not any(squash(domain) in frame_text for domain in load_lines("domains.txt")):
            add(frame[1], "warn", "no-domain", "분야가 정해지지 않았다 — 여덟 분야 중 하나를 적는다")

    # 목표 정의를 모은다.
    goals = {}
    for lineno, line in enumerate(lines, 1):
        definition = GOAL_DEFINITION.match(line)
        if definition:
            goals[definition.group(1)] = (lineno, definition.group(2))

    for goal_id, (lineno, body) in goals.items():
        parent = parent_of(goal_id)
        if parent and parent not in goals:
            add(lineno, "warn", "orphan-goal",
                "%s 의 부모 %s 가 없다 — 위 기간의 목표와 연결이 끊겼다" % (goal_id, parent))
        if not re.search(r"\d|기준", body.replace(goal_id, "")):
            add(lineno, "warn", "unmeasured-goal",
                "%s 에 잴 기준이 없다 — 숫자나 기한을 붙인다" % goal_id)

    for goal_id, (lineno, _) in goals.items():
        if goal_id.startswith("S"):
            continue
        has_child = any(parent_of(other) == goal_id for other in goals)
        if not has_child:
            add(lineno, "note", "childless-goal",
                "%s 아래에 %s 목표가 없다" % (goal_id, "중기" if goal_id.startswith("L") else "단기"))

    # 기능: "기능 정의" 절의 목록 항목마다 목표 번호가 있어야 한다.
    features = next((section for section in sections if "기능 정의" in section[0]), None)
    if features is not None:
        start = features[1]
        for offset, line in enumerate(features[2], 1):
            if not re.match(r"^\s*[-*]\s+", line) or PLACEHOLDER.match(line):
                continue
            references = GOAL_REFERENCE.findall(line)
            if not references:
                add(start + offset, "warn", "unlinked-feature",
                    "어느 목표를 위한 기능인지 없다: %s" % line.strip()[:50])

    # 없는 번호를 가리키는 곳. 정의 줄 자체의 번호는 빼고 본다.
    for lineno, line in enumerate(lines, 1):
        definition = GOAL_DEFINITION.match(line)
        own = definition.group(1) if definition else None
        for reference in GOAL_REFERENCE.findall(line):
            if reference != own and reference not in goals and not PLACEHOLDER.match(line):
                if "<" in line and ">" in line:
                    continue   # 틀의 자리표시 안의 예시 번호다
                add(lineno, "warn", "unknown-goal", "%s 라는 목표는 정의되지 않았다" % reference)

    return [item for item in sorted(found) if show_notes or item[1] == "warn"]


def main(argv=None):
    """명령줄 입구. 경고가 있으면 1로 끝낸다."""
    parser = argparse.ArgumentParser(description="기획서의 틀과 목표 연결을 검사한다.")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--all", action="store_true", help="참고 등급까지 보여준다")
    options = parser.parse_args(argv)

    warning_count = 0
    for path in options.files:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as error:
            print("읽을 수 없다: %s (%s)" % (path, error), file=sys.stderr)
            continue
        for lineno, severity, code, message in check(path, text, options.all):
            print("%s:%d [%s] %s" % (path, lineno, code, message))
            warning_count += severity == "warn"
    print("planner: 경고 %d건 — 파일 %d개" % (warning_count, len(options.files)))
    return 1 if warning_count else 0


if __name__ == "__main__":
    sys.exit(main())
