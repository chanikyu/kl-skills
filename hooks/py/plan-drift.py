#!/usr/bin/env python3
"""계획이 걸린 일을 하는 동안, 일이 계획에서 벗어나는지 알린다.

두 순간에 돈다.

  계획서를 쓸 때   PostToolUse(Write|Edit) 로 직접 불린다. 목표 번호가 정의된 문서이면
                   구조 검사(check_plan)와 이탈 검사(check_drift)를 같이 돌린다
  커밋했을 때      Bash 뒤 Rust 게이트가 'git commit' 을 보면 --plain 으로 이걸 부른다.
                   저장소 안의 계획서를 찾아 이탈 검사를 돌리고, 방금 커밋이 계획 밖인지 알린다

커밋 쪽을 Rust 게이트에 붙인 것은 비용 때문이다. Bash 는 가장 자주 쓰는 도구라서, Python 게이트를
하나 더 걸면 Bash 마다 런처 비용을 두 번 낸다. Rust 쪽이 명령어에서 'git commit' 을 찾는 것은
거의 공짜이고, 진짜 커밋일 때만 이 스크립트가 뜬다.

막지 않는다. 이탈은 판단이 필요한 일이라서 기계가 막을 대상이 아니다.
"""

import json
import os
import re
import subprocess
import sys

from _hook_output import tell_model

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(PLUGIN_ROOT, "skills", "planner", "scripts")
# 목표 번호 뒤에 실제 내용이 있어야 계획서다. 틀의 "[L1] <목표>" 같은 자리표시는 계획이 아니다 —
# 2026-11-11 에 기획서 틀 하나 때문에 리포의 커밋 24건이 전부 '계획 밖' 으로 잡혔다.
GOAL_DEFINITION = re.compile(r"^\s*[-*]\s*\[L\d+\]\s*[^<\s]", re.MULTILINE)
# 커밋한 폴더를 명령에서 찾는다: "git -C 폴더 ..." 와 "cd 폴더 && ..." 두 모양.
FOLDER_IN_COMMAND = re.compile(r"""(?:\bgit\s+-C\s+|(?:^|&&|;|\|\|)\s*cd\s+)("[^"]+"|'[^']+'|\S+)""")
MAX_FILES = 300            # ponytail: 저장소의 .md 를 이만큼만 훑는다. 넘으면 계획서 위치 규약이 필요하다
MAX_BYTES = 200_000        # 한 파일에서 이만큼만 읽는다. 계획서가 이보다 크면 쪼개는 게 맞다


def is_plan(path):
    """목표 번호(L1 등)가 정의된 문서인가. 그것이 이 스킬의 계획서라는 유일한 표시다."""
    if not path.endswith(".md") or not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return bool(GOAL_DEFINITION.search(handle.read(MAX_BYTES)))
    except OSError:
        return False


def plans_in_repo(folder):
    """저장소가 추적하는 .md 가운데 계획서인 것들. 저장소가 아니면 빈 목록이다."""
    try:
        listed = subprocess.run(["git", "-C", folder, "ls-files", "-z", "*.md"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
        top = subprocess.run(["git", "-C", folder, "rev-parse", "--show-toplevel"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    root = (top.stdout or b"").decode().strip()
    if not root:
        return []
    names = [name for name in (listed.stdout or b"").decode("utf-8", "replace").split("\0") if name]
    return [os.path.join(root, name) for name in names[:MAX_FILES]
            if is_plan(os.path.join(root, name))]


def commit_folder(event):
    """커밋이 일어난 폴더. 명령에 적힌 폴더가 먼저고, 없으면 세션 폴더다.

    세션 폴더만 보면 "cd 다른저장소 && 커밋" 이 세션 폴더의 저장소로 잘못 읽힌다
    (2026-11-11 에 실제로 다른 저장소의 계획서를 검사했다).
    """
    base = event.get("cwd") or os.getcwd()
    command = (event.get("tool_input") or {}).get("command") or ""
    for match in FOLDER_IN_COMMAND.finditer(command):
        folder = os.path.expanduser(match.group(1).strip("\"'"))
        if not os.path.isabs(folder):
            folder = os.path.join(base, folder)
        if os.path.isdir(folder):
            return folder
    return base


def run_script(name, args):
    """계획 검사 스크립트를 돌려 (종료 코드, 출력) 을 돌려준다. 실패하면 (0, '') 이다."""
    try:
        finished = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)] + args,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return 0, ""
    return finished.returncode, (finished.stdout or b"").decode("utf-8", "replace").strip()


def main():
    """사건을 읽고, 해당하는 검사를 돌려, 경고가 있을 때만 알린다. 늘 0으로 끝난다."""
    plain = "--plain" in sys.argv
    raw_payload = sys.stdin.read()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0

    reports = []
    file_path = (event.get("tool_input") or {}).get("file_path") or ""
    if file_path and is_plan(file_path):
        # 계획서를 쓴 순간: 틀이 지켜졌는지와 일이 따라가는지를 같이 본다.
        for name, extra in (("check_plan.py", []), ("check_drift.py", [])):
            code, output = run_script(name, extra + [file_path])
            if code:
                reports.append(output)
    elif plain:
        # 커밋한 순간: 저장소의 계획서마다, 방금 커밋까지 포함해 이탈을 본다.
        for plan in plans_in_repo(commit_folder(event)):
            code, output = run_script("check_drift.py", ["--latest-commit", plan])
            if code:
                reports.append(output)

    if not reports:
        return 0
    text = "\n\n".join(reports) + "\n(planner: 일과 계획 중 어느 쪽을 고칠지 정할 자리다. 막지는 않는다)"
    if plain:
        print(text)
    else:
        tell_model("PostToolUse", text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
