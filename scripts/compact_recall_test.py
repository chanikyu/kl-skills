#!/usr/bin/env python3
"""Does an earlier auto-compaction make Claude forget early details? Measure it on a real session.

The token estimate (token_replay.py) says capping the conversation at about 250k tokens would cut
reads by about 60%. That only holds if answers stay as good after the compaction. This runs one
recorded session twice, both times as a fork (--fork-session) so the original is never changed:

  A  resume as it is, ask the recall questions
  B  resume with CLAUDE_AUTOCOMPACT_PCT_OVERRIDE set below the session's size, so Claude Code
     compacts before answering, then ask the same questions

Answers must come from memory: file and shell tools are denied, and the kl-skills plugin is turned
off for the run so its hooks do not add turns. Each answer line is graded against the question's
accepted forms. Claude Code reports a resumed session's cost cumulatively (the original requests
included), so the cost column is cumulative; work out the new spend from the token deltas.
Everything goes to --out: the prompt, each arm's raw JSON, the forked transcript's
compaction evidence, and a TSV with one row per question and arm.

  compact_recall_test.py --session 849d6912-... --cwd ~/workspace/kl-skills \\
      --questions questions.json --cap-pct 25 --out results/compact-recall_849d6912_cap25
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import unicodedata

DENIED_TOOLS = "Bash Read Grep Glob Write Edit MultiEdit NotebookEdit WebFetch WebSearch Agent Task"
PLUGIN_OFF = {"enabledPlugins": {"kl-skills@kl-skills": False}}
UNKNOWN_MARKS = ("모름", "모르", "기억나지", "unknown", "not sure")


def build_prompt(items):
    """질문 묶음을 한 번에 묻는 글. 번호마다 한 줄로, 도구 없이 기억으로만 답하게 한다."""
    lines = ["이 대화에서 기억하는 내용만으로 아래 질문에 답하라. 파일을 열거나 도구를 쓰지 마라.",
             "모르면 '모름'이라고 쓴다. 번호마다 한 줄, 답만 짧게 쓴다.", ""]
    lines += ["%d. %s" % (item["id"], item["question"]) for item in items]
    return "\n".join(lines)


def run_arm(name, args, prompt, env_extra):
    """한 갈래를 비대화로 돌려 결과 JSON(마지막 result 항목)을 돌려준다. 원본 JSON 은 파일로 남긴다."""
    command = ["claude", "-p", prompt, "--resume", args.session, "--fork-session",
               "--settings", json.dumps(PLUGIN_OFF), "--disallowedTools", DENIED_TOOLS,
               "--output-format", "json"]
    env = dict(os.environ, **env_extra)
    finished = subprocess.run(command, cwd=os.path.expanduser(args.cwd), env=env, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=args.timeout)
    with open(os.path.join(args.out, "arm-%s_raw.json" % name), "w", encoding="utf-8") as handle:
        handle.write(finished.stdout)
    with open(os.path.join(args.out, "arm-%s_stderr.log" % name), "w", encoding="utf-8") as handle:
        handle.write(finished.stderr)
    parsed = json.loads(finished.stdout)
    events = parsed if isinstance(parsed, list) else [parsed]
    final_event = next((event for event in reversed(events) if event.get("type") == "result"), {})
    if not final_event:
        raise RuntimeError("arm %s: no result in output (exit %d)" % (name, finished.returncode))
    return final_event


def compaction_events(session_id, projects):
    """갈래 세션의 기록에서 압축 흔적(압축 요약 줄, compact 경계) 수를 센다."""
    paths = glob.glob(os.path.join(projects, "*", session_id + ".jsonl"))
    if not paths:
        return None
    count = 0
    with open(paths[0], encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if '"isCompactSummary": true' in line or '"isCompactSummary":true' in line or "compact_boundary" in line:
                count += 1
    return count


def normalise(text):
    """맞춰 보기 전에 글자 모양을 맞춘다: 유니코드 정규화, 소문자, 따옴표·백틱·공백 정리."""
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", re.sub(r"[`'\"“”‘’]", "", text)).strip()


def answer_lines(text, count):
    """답 글에서 '번호. 답' 줄을 {번호: 답} 으로."""
    found = {}
    for line in text.splitlines():
        match = re.match(r"^\s*(\d+)[.)]\s*(.*)$", line)
        if match and 1 <= int(match.group(1)) <= count:
            found.setdefault(int(match.group(1)), match.group(2).strip())
    return found


def grade(item, answer):
    """정답 형태 중 하나라도 답에 들어 있으면 correct, 모른다고 하면 unknown, 아니면 wrong."""
    said = normalise(answer or "")
    forms = [normalise(item["answer"])] + [normalise(form) for form in item.get("accept", [])]
    if any(form and form in said for form in forms):
        return "correct"
    if not said or any(mark in said for mark in UNKNOWN_MARKS):
        return "unknown"
    return "wrong"


def main():
    """두 갈래를 돌려 채점하고, 정답률·토큰·비용을 표로 남긴다."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--session", required=True)
    parser.add_argument("--cwd", required=True, help="the folder the session was recorded in")
    parser.add_argument("--questions", required=True, help="JSON with items: id, question, answer, accept")
    parser.add_argument("--cap-pct", type=float, required=True, help="CLAUDE_AUTOCOMPACT_PCT_OVERRIDE for arm B")
    parser.add_argument("--out", required=True)
    parser.add_argument("--projects", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with open(args.questions, encoding="utf-8") as handle:
        items = json.load(handle)["items"]
    prompt = build_prompt(items)
    with open(os.path.join(args.out, "prompt.txt"), "w", encoding="utf-8") as handle:
        handle.write(prompt)
    arms = {"A-as-is": {}, "B-compacted": {"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "%g" % args.cap_pct}}
    rows, summary = [], []
    # 두 갈래는 같은 질문·같은 도구 제한이고, 다른 것은 압축 기준 환경 변수 하나뿐이다
    for name, env_extra in arms.items():
        final_event = run_arm(name, args, prompt, env_extra)
        answers = answer_lines(final_event.get("result") or "", len(items))
        grades = {item["id"]: grade(item, answers.get(item["id"])) for item in items}
        usage = final_event.get("usage") or {}
        compactions = compaction_events(final_event.get("session_id", ""), args.projects)
        summary.append((name, sum(mark == "correct" for mark in grades.values()), sum(mark == "unknown" for mark in grades.values()),
                        len(items), usage.get("cache_creation_input_tokens", 0), usage.get("cache_read_input_tokens", 0),
                        usage.get("output_tokens", 0), final_event.get("total_cost_usd"), compactions, final_event.get("session_id")))
        rows += [(name, item["id"], grades[item["id"]], item["answer"], answers.get(item["id"], "")) for item in items]
    with open(os.path.join(args.out, "grades.tsv"), "w", encoding="utf-8") as handle:
        handle.write("arm\tid\tgrade\texpected\tanswered\n")
        handle.writelines("\t".join(str(cell).replace("\t", " ") for cell in row) + "\n" for row in rows)
    with open(os.path.join(args.out, "summary.tsv"), "w", encoding="utf-8") as handle:
        handle.write("arm\tcorrect\tunknown\tquestions\tcache_write\tcache_read\toutput\tcumulative_cost_usd\tcompaction_events\tfork_session\n")
        handle.writelines("\t".join(str(cell) for cell in row) + "\n" for row in summary)
    for row in summary:
        print("%-12s correct %d/%d  unknown %d  cache_write %d  cache_read %d  output %d  cost %s  compactions %s"
              % (row[0], row[1], row[3], row[2], row[4], row[5], row[6], row[7], row[8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
