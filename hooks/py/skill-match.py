#!/usr/bin/env python3
"""UserPromptSubmit gate: tell the model which kl-skills skill this message is for.

A skill loads when the model decides the conversation matches its description —
which is not guaranteed. Asked on 2026-11-13: "llm-wiki-docs, research-to-wiki,
planner, pipeline-debug — do they only work if I name them?" This gate matches
the message against each skill's own trigger list (the "Triggers" part of the
description in its SKILL.md — the one source, never copied here) and, when a
skill clearly matches, attaches "use this skill".

Noise control, both from data files in hooks/data/:
  skill-match-generic.txt   trigger words too common to count (name, code, 정리 …)
  skill-match-skip.txt      skills a hook already applies every turn
A skill is suggested when its matched triggers score at least MIN_SCORE. A
narrow trigger counts 2: a phrase of two or more words, a Korean trigger of three
or more letters, or an English word of LONG_WORD_LETTERS or more (research,
roadmap); anything else counts 1. The skill's own name in the message ("plan it
with the planner") counts 2 as well. At most MAX_SUGGESTIONS skills are named.
Only English and Korean trigger words exist; in other languages the model still
matches the description itself.
"""

import glob
import json
import os
import re
import sys

from _hook_output import read_payload, tell_model

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PLUGIN_ROOT, "hooks", "data")
PLUGIN_NAME = "kl-skills"
MIN_SCORE = int(os.environ.get("SKILL_MATCH_MIN_SCORE", "2"))
MAX_SUGGESTIONS = 2
MIN_PROMPT_CHARS = 6        # "그래", "확인해줘" 같은 짧은 말에는 붙이지 않는다
# 이 길이 이상의 영어 낱말은 뜻이 좁다(긴 도구 이름, 방법 이름). 2026-11-13 위키 예시 문장
# "Research whether X causes Y" 가 한 낱말 1점이라 안 붙었다.
LONG_WORD_LETTERS = 6
TRIGGERS = re.compile(r"Triggers?\s*[-:]\s*(.+)$", re.IGNORECASE)
HANGUL = re.compile(r"[가-힣]")


def load_words(file_name):
    """데이터 파일의 낱말 집합(소문자). # 줄과 빈 줄은 뺀다. 파일이 없으면 빈 집합."""
    try:
        with open(os.path.join(DATA_DIR, file_name), encoding="utf-8") as handle:
            return {line.strip().lower() for line in handle if line.strip() and not line.startswith("#")}
    except OSError:
        return set()


def skill_triggers():
    """{스킬 이름: [발동 말, ...]} — 각 SKILL.md 앞머리 description 의 Triggers 목록에서 읽는다."""
    found = {}
    for path in sorted(glob.glob(os.path.join(PLUGIN_ROOT, "skills", "*", "SKILL.md"))):
        try:
            with open(path, encoding="utf-8") as handle:
                head = handle.read(8000)
        except OSError:
            continue
        description = next((line[len("description:"):] for line in head.splitlines()
                            if line.startswith("description:")), "")
        match = TRIGGERS.search(description)
        if match:
            words = [word.strip().strip(".").strip() for word in match.group(1).split(",")]
            found[os.path.basename(os.path.dirname(path))] = [word for word in words if word]
    return found


def trigger_weight(trigger):
    """두 낱말 이상의 말이나 세 글자 이상의 한국어 말은 뜻이 좁아서 2점, 나머지는 1점."""
    if len(trigger.split()) >= 2 or len(HANGUL.findall(trigger)) >= 3:
        return 2
    if not HANGUL.search(trigger) and len(trigger) >= LONG_WORD_LETTERS:
        return 2
    return 1


def matches(trigger, lowered_prompt):
    """메시지에 그 발동 말이 있나. 영어는 낱말 단위로, 한국어는 붙은 조사째로 찾는다."""
    if HANGUL.search(trigger):
        return trigger in lowered_prompt
    return re.search(r"(?<![a-z0-9])" + re.escape(trigger) + r"(?![a-z0-9])", lowered_prompt) is not None


def suggestions(prompt):
    """[(스킬, 점수, 맞은 말들)] 중 기준을 넘는 것을 점수 순으로."""
    lowered = prompt.lower()
    generic, skipped = load_words("skill-match-generic.txt"), load_words("skill-match-skip.txt")
    ranked = []
    for skill, triggers in skill_triggers().items():
        if skill in skipped:
            continue
        hits = sorted({trigger for trigger in triggers
                       if trigger.lower() not in generic and matches(trigger.lower(), lowered)})
        score = sum(trigger_weight(hit) for hit in hits)
        # 스킬 이름을 직접 말했으면("planner 로 기획해줘") 그것만으로 충분한 신호다.
        if matches(skill.lower(), lowered):
            hits.append(skill)
            score += 2
        if score >= MIN_SCORE:
            ranked.append((skill, score, hits))
    ranked.sort(key=lambda item: -item[1])
    return ranked[:MAX_SUGGESTIONS]


def main():
    """메시지와 맞는 스킬이 있으면 알린다. 없으면 조용하다. 늘 0으로 끝난다."""
    raw_payload = read_payload()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0
    prompt = str(event.get("prompt") or "").strip() if isinstance(event, dict) else ""
    if len(prompt) < MIN_PROMPT_CHARS:
        return 0
    found = suggestions(prompt)
    if not found:
        return 0
    lines = ["skill-match: 이 메시지에 맞는 스킬이 있다. Skill 도구로 불러 그 지침을 따른다 (맞지 않으면 무시)."]
    for skill, _, hits in found:
        lines.append("  - %s:%s  (맞은 말: %s)" % (PLUGIN_NAME, skill, ", ".join(hits)))
    tell_model("UserPromptSubmit", "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
