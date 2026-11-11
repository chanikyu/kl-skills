#!/usr/bin/env python3
"""훅 하나를 실제 대화 기록에 대고, 사람 메시지마다 "그때 이 훅이 뭐라고 했을지" 다시 돌린다.

    replay.py GATE --transcript 기록.jsonl --out 결과.tsv [--event stop|prompt] [--last N]

테스트 입력은 만든 사람이 상상한 대화다. 실제 대화에는 상상 못 한 것이 섞여 있다 — 요약문,
규칙 묶음, 6초 간격으로 두 번 들어온 같은 메시지. 2026-11-11 answer-check 를 고칠 때 이
세션 기록 40개 메시지로 다시 판정해 본 것이 테스트보다 결함을 더 많이 찾았다. 그 일을
일회용 코드 대신 명령 한 줄로 만든 것이 이 스크립트다.

시점을 자르는 방법:

  stop    턴이 끝난 시점. 사람 메시지 하나와 그에 대한 답까지 (다음 사람 메시지 직전까지)
          Stop 훅(answer-check, wiki-sync)이 보는 상태다
  prompt  사람이 메시지를 보낸 시점. 그 메시지는 기록에 아직 없고 prompt 로 따로 온다
          UserPromptSubmit 훅(wiki-recall)이 보는 상태다

훅은 Claude Code 와 같은 방법으로 부른다: sh <플러그인>/hooks/run.sh <GATE>, 입력은 stdin JSON.
결과는 시점마다 한 줄씩 TSV 로 남긴다. 화면에만 띄우면 다시 볼 수 없다.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_TIMEOUT_SECONDS = 60   # hooks.json 에서 가장 긴 제한(120초)의 절반. 넘으면 그 시점만 timeout 으로 적는다
EXCERPT_CHARS = 200         # 결과 표 한 칸에 담는 글자 수. 더 길면 표가 읽히지 않는다
EVENT_NAMES = {"stop": "Stop", "prompt": "UserPromptSubmit"}


def load_transcript_reader(plugin_root):
    """훅과 같은 '사람 메시지 판정' 코드를 불러온다. 베껴 쓰면 둘이 어긋난다."""
    sys.path.insert(0, os.path.join(plugin_root, "hooks", "py"))
    import _transcript  # noqa: E402 — 경로를 넣은 뒤에만 찾을 수 있다
    return _transcript


def human_message_lines(raw_lines, transcript_module):
    """사람이 쓴 메시지가 몇 번째 줄에 있는지와 그 글. [(줄 번호, 글), ...]"""
    found = []
    for line_number, line in enumerate(raw_lines):
        turn = transcript_module.classify_line(line)
        if turn and turn[0] == "user":
            found.append((line_number, turn[1]))
    return found


def cut_points(human_lines, total_lines, event):
    """시점마다 (기록을 몇 줄까지 쓸지, 그 시점의 사람 메시지). 시점을 자르는 규칙은 맨 위 설명."""
    points = []
    for index, (line_number, text) in enumerate(human_lines):
        if event == "prompt":
            points.append((line_number, text))
        else:
            next_human = human_lines[index + 1][0] if index + 1 < len(human_lines) else total_lines
            points.append((next_human, text))
    return points


def run_gate(plugin_root, gate, payload):
    """훅을 Claude Code 와 같은 방법으로 한 번 부른다. (종료 코드, 출력, 걸린 초)"""
    environment = dict(os.environ, CLAUDE_PLUGIN_ROOT=plugin_root)
    launcher = os.path.join(plugin_root, "hooks", "run.sh")
    started = time.monotonic()
    try:
        finished = subprocess.run(["sh", launcher, gate], input=json.dumps(payload, ensure_ascii=False),
                                  capture_output=True, text=True, env=environment,
                                  timeout=GATE_TIMEOUT_SECONDS)
        return finished.returncode, (finished.stdout or "").strip(), time.monotonic() - started
    except subprocess.TimeoutExpired:
        return "timeout", "", time.monotonic() - started


def one_line(text):
    """표 한 칸에 들어가게 줄바꿈·탭을 펴고 길이를 자른다."""
    flat = " ".join(text.split())
    return flat if len(flat) <= EXCERPT_CHARS else flat[:EXCERPT_CHARS] + "…"


def replay(options):
    """시점마다 훅을 돌리고 결과 행 목록을 돌려준다."""
    transcript_module = load_transcript_reader(options.plugin_root)
    with open(options.transcript, encoding="utf-8", errors="replace") as handle:
        raw_lines = handle.readlines()
    human_lines = human_message_lines(raw_lines, transcript_module)
    points = cut_points(human_lines, len(raw_lines), options.event)
    first_turn = max(0, len(points) - options.last) if options.last else 0

    rows = []
    with tempfile.TemporaryDirectory() as work_folder:
        for turn_number in range(first_turn, len(points)):
            line_count, message = points[turn_number]
            # 그 시점까지의 기록만 담은 파일을 만들어 훅에 넘긴다. 원본 기록은 건드리지 않는다.
            cut_path = os.path.join(work_folder, "turn-%04d.jsonl" % (turn_number + 1))
            with open(cut_path, "w", encoding="utf-8") as cut_file:
                cut_file.writelines(raw_lines[:line_count])
            payload = {"hook_event_name": EVENT_NAMES[options.event], "session_id": "hook-replay",
                       "transcript_path": cut_path, "cwd": options.cwd, "stop_hook_active": False}
            if options.event == "prompt":
                payload["prompt"] = message
            exit_code, output, seconds = run_gate(options.plugin_root, options.gate, payload)
            rows.append({"turn": turn_number + 1, "fired": "yes" if output else "no",
                         "exit_code": exit_code, "seconds": "%.2f" % seconds,
                         "message": one_line(message), "output": one_line(output)})
    return rows, len(points)


def parse_arguments(argv):
    """명령줄 인자. 결과 파일 경로는 꼭 받는다 — 화면에만 남은 결과는 다시 볼 수 없다."""
    parser = argparse.ArgumentParser(description="훅을 실제 대화 기록의 시점마다 다시 돌린다")
    parser.add_argument("gate", help="hooks/run.sh 에 넘기는 게이트 이름. 예: answer-check, wiki-recall")
    parser.add_argument("--transcript", required=True, help="대화 기록 JSONL")
    parser.add_argument("--out", required=True, help="결과 TSV 경로. 이름에 게이트·시점 범위를 넣는다")
    parser.add_argument("--event", choices=sorted(EVENT_NAMES), default="stop",
                        help="stop: 턴이 끝난 시점(기본) / prompt: 메시지를 보낸 시점")
    parser.add_argument("--last", type=int, default=0, help="마지막 N개 시점만 (0이면 전부)")
    parser.add_argument("--plugin-root", default=PLUGIN_ROOT,
                        help="훅을 가져올 플러그인 폴더 (기본: 이 스크립트가 든 플러그인)")
    parser.add_argument("--cwd", default=os.getcwd(), help="훅에 넘길 작업 폴더 (기본: 지금 폴더)")
    return parser.parse_args(argv)


def main(argv=None):
    """다시 돌리고, 표를 쓰고, 몇 번 말했는지 요약을 찍는다."""
    options = parse_arguments(argv)
    if not os.path.isfile(options.transcript):
        print("기록 파일이 없다: %s" % options.transcript, file=sys.stderr)
        return 2
    rows, total_points = replay(options)
    columns = ["turn", "fired", "exit_code", "seconds", "message", "output"]
    with open(options.out, "w", encoding="utf-8", newline="") as out_file:
        # csv 기본 줄끝은 \r\n 이다. awk·cut 으로 읽으면 마지막 칸에 \r 이 붙는다.
        writer = csv.DictWriter(out_file, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    fired = [row for row in rows if row["fired"] == "yes"]
    failed = [row for row in rows if row["exit_code"] != 0]
    print("%s: 시점 %d개 중 %d개를 다시 돌림 — 말한 시점 %d개, 0이 아닌 종료 %d개 → %s"
          % (options.gate, total_points, len(rows), len(fired), len(failed), options.out))
    for row in fired:
        print("  %4d번째 | %s\n         └ %s" % (row["turn"], row["message"][:60], row["output"][:120]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
