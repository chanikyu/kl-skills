#!/usr/bin/env python3
"""코덱스가 파일을 고친 뒤 PostToolUse 훅에 넘기는 입력을 만든다(시험용).

    codex_patch_event.py <작업 폴더> <파일> [<파일>...]

코덱스는 파일 경로 대신 apply_patch 의 패치 글을 tool_input.command 에 넣는다. 경로는 작업 폴더
기준이고 파일마다 머리 줄이 하나다. 모양은 openai/codex 의 codex-rs/core/src/tools/handlers/
apply_patch.rs 와 codex-rs/core/tests/suite/hooks.rs 를 따랐다(2026-11-20 확인).
"""
import json
import sys


def main():
    """받은 파일마다 Update File 머리 줄을 단 패치로 사건 JSON 한 줄을 찍는다."""
    cwd, files = sys.argv[1], sys.argv[2:]
    patch = "*** Begin Patch\n" + "".join(
        "*** Update File: %s\n@@\n-old line\n+new line\n" % name for name in files) + "*** End Patch"
    print(json.dumps({"hook_event_name": "PostToolUse", "tool_name": "apply_patch", "cwd": cwd,
                      "tool_input": {"command": patch}, "tool_response": "Success."}))


if __name__ == "__main__":
    main()
