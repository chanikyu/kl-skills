#!/usr/bin/env python3
"""문헌 조사로 쓴 위키 페이지가 "어디까지 확인된 말인지"를 드러내는지 검사한다.

    check_research.py [--exit-zero] PAGE.md [PAGE.md ...]

조사 페이지에서 가장 쉽게 빠지는 것은 두 가지다. 하나는 그 근거가 어떤 연구인지 —
쥐 실험과 사람 시험이 같은 무게로 읽히면 결론이 부풀려진다. 다른 하나는 내가 어디까지
읽었는지 — 초록만 읽고 쓴 숫자를 본문에서 확인한 것처럼 옮기게 된다. 2026-11-11 장내
미생물 조사에서 둘 다 손으로 적었다. 이 검사는 그 두 표시가 빠진 출처를 잡는다.

출처 줄의 모양 (## 출처 아래):

    - [저자 연도] 한 줄 설명. 학술지. <주소> — 근거 수준 · 읽은 수준

근거 수준과 읽은 수준에 쓸 수 있는 이름은 data/ 의 두 파일에 있다. 코드에 적지 않는다.
"""

import argparse
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
SOURCES_HEADING = re.compile(r"^##\s+출처\s*$")
SOURCE_ENTRY = re.compile(r"^[-*]\s+\[([^\]\n]+)\]")
LEVEL_TAIL = re.compile(r"[—–-]\s*([^—–·\n]+?)\s*·\s*([^·\n]+?)\s*$")
LINK = re.compile(r"https?://|doi\.org/|<[^>\s]+>")
# 본문의 인용: [저자 연도] 또는 [저자 연도, 저자 연도]. 마크다운 링크 [글](주소)는 인용이 아니다.
CITATION = re.compile(r"\[([^\]\n]*\b(?:1[89]|20)\d{2}[a-z]?)\](?!\()")


def load_names(file_name, tsv=False):
    """데이터 파일에서 이름 목록을 파일 순서대로 읽는다. # 줄은 설명이고, TSV 면 첫 열만 쓴다(머리줄 제외)."""
    names = []
    with open(os.path.join(DATA_DIR, file_name), encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            names.append(line.split("\t")[0].strip() if tsv else line.strip())
    return names[1:] if tsv else names


def split_page(lines):
    """(본문 줄들, 출처 줄들, 출처 제목이 있었나). 각 줄은 (줄 번호, 글)."""
    body, sources, in_sources, has_heading = [], [], False, False
    for number, line in enumerate(lines, 1):
        if SOURCES_HEADING.match(line.strip()):
            in_sources, has_heading = True, True
            continue
        # 출처 절은 다음 같은 급(##) 제목에서 끝난다.
        if in_sources and line.startswith("## "):
            in_sources = False
        (sources if in_sources else body).append((number, line))
    return body, sources, has_heading


def conclusion_comes_first(body):
    """제목 다음 첫 글이 문장인가. 목록·표·소제목으로 시작하면 결론이 앞에 없는 것이다."""
    seen_title = False
    for number, line in body:
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_title and stripped.startswith("# "):
            seen_title = True
            continue
        if re.match(r"^(#|[-*|>]|\d+[.)])", stripped):
            return number
        return None
    return None


def check_page(path, evidence_levels, reading_levels):
    """페이지 하나의 지적 목록 [(줄 번호, 코드, 설명)]."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    body, sources, has_heading = split_page(lines)
    found = []
    first_line = conclusion_comes_first(body)
    if first_line:
        found.append((first_line, "conclusion-not-first",
                      "제목 바로 다음이 결론 문장이 아니다. 질문의 낱말로 답하는 한두 문장을 맨 앞에 둔다"))
    if not has_heading:
        found.append((1, "missing-sources", "'## 출처' 절이 없다. 근거 없는 조사 페이지는 다시 확인할 수 없다"))

    source_keys = {}
    for number, line in sources:
        entry = SOURCE_ENTRY.match(line.strip())
        if not entry:
            continue
        source_keys[entry.group(1).strip()] = number
        if not LINK.search(line):
            found.append((number, "source-missing-link", "출처에 주소(DOI·URL)가 없다"))
        tail = LEVEL_TAIL.search(line)
        if not tail:
            # 예시도 데이터 파일의 이름으로 만든다. 코드에 이름을 적으면 목록과 어긋난다.
            found.append((number, "source-missing-levels",
                          "출처 끝에 '— 근거 수준 · 읽은 수준' 이 없다. 예: — %s · %s"
                          % (evidence_levels[0], reading_levels[0])))
            continue
        evidence, reading = tail.group(1).strip(), tail.group(2).strip()
        if evidence not in evidence_levels:
            found.append((number, "unknown-evidence-level",
                          "근거 수준 '%s' 는 목록에 없다: %s" % (evidence, ", ".join(evidence_levels))))
        if reading not in reading_levels:
            found.append((number, "unknown-reading-level",
                          "읽은 수준 '%s' 는 목록에 없다: %s" % (reading, ", ".join(reading_levels))))

    # 본문에서 쓴 인용과 출처 목록을 맞춘다. 한쪽에만 있으면 독자가 근거를 못 찾는다.
    cited = set()
    for number, line in body:
        for group in CITATION.findall(line):
            for key in (part.strip() for part in group.split(",")):
                cited.add(key)
                if source_keys and key not in source_keys:
                    found.append((number, "citation-without-source", "인용 [%s] 가 출처 목록에 없다" % key))
    for key, number in source_keys.items():
        if key not in cited:
            found.append((number, "source-not-cited", "출처 [%s] 를 본문에서 한 번도 인용하지 않았다" % key))
    return found


def main(argv=None):
    """페이지들을 검사해 줄마다 지적을 찍는다. 지적이 있으면 1 (--exit-zero 면 0)."""
    parser = argparse.ArgumentParser(description="조사 페이지의 근거·읽은 수준 표시를 검사한다")
    parser.add_argument("pages", nargs="+")
    parser.add_argument("--exit-zero", action="store_true", help="지적이 있어도 0으로 끝낸다(훅용)")
    options = parser.parse_args(argv)
    evidence_levels = load_names("evidence-levels.tsv", tsv=True)
    reading_levels = load_names("reading-levels.txt")
    total = 0
    for path in options.pages:
        for number, code, message in check_page(path, evidence_levels, reading_levels):
            print("%s:%d [%s] %s" % (path, number, code, message))
            total += 1
    print("research-to-wiki: 지적 %d건 — 파일 %d개" % (total, len(options.pages)))
    return 0 if options.exit_zero or total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
