#!/usr/bin/env python3
"""PreToolUse gate (Bash): keep long command output out of the conversation.

Every request re-reads the whole conversation, so a 5,000-line test log printed once is paid for
on every later request of the session. This gate rewrites the Bash command (updatedInput, no
permission decision, so the user's permission rules still apply) so that its output goes to a
file. When the output is short the file is printed as it is. When it is long, only the first and
last lines stay in the conversation, with the file's path so the full text can be grepped or read
with an offset. The exit code is kept.

Left alone, because wrapping could break them: background runs, and commands with exit, exec,
return, set -e / errexit, or a trailing & (a background job).

Settings, from the environment (defaults below):
  KL_OFFLOAD=0               turn the gate off
  KL_OFFLOAD_DIR             where full outputs go (default ~/.claude/tool-outputs/<session>)
  KL_OFFLOAD_MAX_BYTES       output up to this size is printed whole
  KL_OFFLOAD_HEAD / _TAIL    lines kept from the start / end of a long output
  KL_OFFLOAD_LINE_CHARS      a kept line longer than this is cut
Asked for on 2026-11-16: cut token use by forcing it, not by asking the model to remember.

Status: experimental, NOT registered in hooks/hooks.json. Replaying 40 recorded sessions
(scripts/token_replay.py, results/token-replay_30d_*_20261116.tsv) put its saving at 0.5-1.0%:
long Bash output is rarely what fills the conversation. It is kept because token_replay.py reads
its thresholds from here; enable it per project with a PreToolUse hook on Bash if a workload
prints large logs.
"""

import json
import os
import re
import sys

from _hook_output import read_payload

DEFAULTS = {"KL_OFFLOAD_MAX_BYTES": 6000,   # 약 1,500 토큰. 이보다 짧으면 통째로 보여 준다
            "KL_OFFLOAD_HEAD": 40,
            "KL_OFFLOAD_TAIL": 30,
            "KL_OFFLOAD_LINE_CHARS": 300}
# 감싸면 셸이 먼저 끝나 버려 출력이 사라질 수 있는 명령(exit·exec·return·errexit)과 백그라운드 작업
RISKY = re.compile(r"(?:^|[\s;&|(){}])(?:exit|exec|return)(?:\s|;|$)|set\s+-[A-Za-z]*e|errexit|&\s*$")


def setting(name):
    """환경 변수 값(정수). 없거나 숫자가 아니면 기본값."""
    try:
        return int(os.environ.get(name, DEFAULTS[name]))
    except ValueError:
        return DEFAULTS[name]


def output_dir(session_id):
    """전체 출력을 둘 폴더. 세션 id 에서 파일 이름에 못 쓰는 글자는 뺀다."""
    base = os.environ.get("KL_OFFLOAD_DIR")
    if base:
        return base
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", str(session_id or "")) or "unknown"
    return os.path.join(os.path.expanduser("~"), ".claude", "tool-outputs", safe_id)


def wrapped(command, folder):
    """명령을 감싼다: 출력을 파일로 보내고, 길면 앞뒤와 경로만 찍는다. 같은 셸에서 돌아 cd 가 이어진다."""
    quoted = "'" + folder.replace("'", "'\\''") + "'"
    return (
        "mkdir -p %(dir)s; __kl_out=%(dir)s/\"$(date +%%Y%%m%%d-%%H%%M%%S)-$$-$RANDOM.log\"\n"
        "{ %(cmd)s\n} > \"$__kl_out\" 2>&1\n"
        "__kl_status=$?\n"
        "__kl_bytes=$(wc -c < \"$__kl_out\" | tr -d ' ')\n"
        "if [ \"$__kl_bytes\" -le %(max)d ]; then cat \"$__kl_out\"; else\n"
        "  head -n %(head)d \"$__kl_out\" | cut -c1-%(chars)d\n"
        "  printf '\\n... [kl-skills offload: %%s lines, %%s bytes in total. Full output: %%s — grep it, or read it with an offset]\\n\\n'"
        " \"$(wc -l < \"$__kl_out\" | tr -d ' ')\" \"$__kl_bytes\" \"$__kl_out\"\n"
        "  tail -n %(tail)d \"$__kl_out\" | cut -c1-%(chars)d\n"
        "fi\n"
        "(exit $__kl_status)"
    ) % {"dir": quoted, "cmd": command, "max": setting("KL_OFFLOAD_MAX_BYTES"),
         "head": setting("KL_OFFLOAD_HEAD"), "tail": setting("KL_OFFLOAD_TAIL"),
         "chars": setting("KL_OFFLOAD_LINE_CHARS")}


def main():
    """Bash 호출이면 명령을 감싸서 updatedInput 으로 돌려준다. 그 밖에는 조용하다. 늘 0으로 끝난다."""
    try:
        event = json.loads(read_payload() or "{}")
    except ValueError:
        return 0
    if not isinstance(event, dict) or os.environ.get("KL_OFFLOAD") == "0":
        return 0
    tool_input = event.get("tool_input")
    if event.get("tool_name") != "Bash" or not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    # 백그라운드 실행은 출력을 나중에 파일로 읽는다 — 이미 대화 밖이다. 위험한 명령은 감싸지 않는다
    if not isinstance(command, str) or not command.strip() or tool_input.get("run_in_background") \
            or RISKY.search(command):
        return 0
    updated = dict(tool_input, command=wrapped(command, output_dir(event.get("session_id"))))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
