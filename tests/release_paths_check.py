"""plugin-release 의 "이 커밋이 CI 를 돌게 하나" 판정을 여러 워크플로 모양으로 확인한다.

selftest-plugin-release.sh 가 부른다. 2026-11-11 리뷰가 재현한 모양들이다 — 줄 단위로 읽다가
모르는 모양을 만나면 "CI 없음" 쪽으로 기울어, CI 를 기다리지 않고 설치할 뻔했다.
원칙: 확실히 읽은 단순한 모양만 경로 조건으로 쓰고, 나머지는 모두 "CI 가 돈다" 로 본다.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile

RELEASE = sys.argv[1]
spec = importlib.util.spec_from_file_location("release", RELEASE)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
failures = 0


def report(passed, message):
    """테스트 한 줄을 셀프테스트 모양으로 찍는다."""
    global failures
    print(("ok    " if passed else "FAIL  ") + message)
    failures += 0 if passed else 1


# --- 워크플로 모양별: 경로 목록 / None(모든 push) / "no-push"
shapes = [
    ("on:\n  push:\n    paths:\n    - 'crates/**'\n", ["crates/**"], "경로 목록을 paths: 와 같은 들여쓰기로 써도 읽는다"),
    ("on:\n  push:\n    paths:\n      - 'crates/**'  # rust\n", ["crates/**"], "경로 항목 끝의 주석은 경로가 아니다"),
    ("on:\n  - push\n", None, "목록으로 쓴 push 는 모든 push 에 돈다"),
    ("on: push # all\n", None, "주석이 붙은 'on: push' 는 모든 push 에 돈다"),
    ("on: [push, pull_request] # x\n", None, "주석이 붙은 'on: [push, ...]' 는 모든 push 에 돈다"),
    ("on:\n  push:  # main\n    paths:\n      - 'a/**'\n", ["a/**"], "push: 뒤의 주석은 무시한다"),
    ("on:\n  push: { branches: [main] }\n", None, "한 줄로 몰아 쓴 push 는 모르는 모양 — CI 가 돈다고 본다"),
    ("on: { push: { paths: ['crates/**'] } }\n", None, "한 줄로 몰아 쓴 on 은 모르는 모양 — CI 가 돈다고 본다"),
    ("on:\n  push:\n    paths: ['a/**']\n", None, "한 줄 목록의 paths 는 모르는 모양 — CI 가 돈다고 본다"),
    ("on:\n  push:\n    paths:\n      - 'a/**'\n      - '!a/doc/**'\n", None, "제외 경로(!)가 있으면 CI 가 돈다고 본다"),
    ("on:\n  pull_request:\n  workflow_dispatch:\n", "no-push", "push 가 아예 없으면 push 때 돌지 않는다"),
]
for text, expected, message in shapes:
    actual = release.push_path_filters(text)
    report(actual == expected, "%s (받은 값: %r)" % (message, actual))

# --- GitHub 경로 규칙: **/ 는 폴더 0개도 맞는다
cases = [("**/Cargo.toml", "Cargo.toml", True), ("docs/**/*.md", "docs/a.md", True),
         ("crates/**", "crates/kl-gate/src/main.rs", True), ("src/*.rs", "src/a/b.rs", False)]
for pattern, path, expected in cases:
    report(release.github_path_matches(pattern, path) == expected,
           "경로 규칙 %s 와 %s → %s" % (pattern, path, expected))


def git(folder, *args):
    """임시 저장소에서 git 을 조용히 돌린다."""
    subprocess.run(["git", "-C", folder, *args], check=True, capture_output=True)


# --- 실제 저장소: 한글 파일 이름, 병합 커밋
with tempfile.TemporaryDirectory() as folder:
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "user.name", "t")
    git(folder, "config", "user.email", "t@example.invalid")
    os.makedirs(os.path.join(folder, ".github", "workflows"))
    with open(os.path.join(folder, ".github", "workflows", "build.yml"), "w") as handle:
        handle.write("on:\n  push:\n    paths:\n      - 'crates/**'\n")
    with open(os.path.join(folder, "README.md"), "w") as handle:
        handle.write("x\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "init")
    os.makedirs(os.path.join(folder, "crates"))
    with open(os.path.join(folder, "crates", "한글 파일.rs"), "w") as handle:
        handle.write("fn main() {}\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "korean name")
    report(release.commit_needs_ci(folder, "HEAD"), "한글·공백이 든 파일 이름도 CI 경로로 맞춘다")

    git(folder, "checkout", "-q", "-b", "side", "HEAD~1")
    with open(os.path.join(folder, "crates_note.txt"), "w") as handle:
        handle.write("x\n")
    os.makedirs(os.path.join(folder, "crates"), exist_ok=True)
    with open(os.path.join(folder, "crates", "b.rs"), "w") as handle:
        handle.write("fn b() {}\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "side")
    git(folder, "checkout", "-q", "main")
    git(folder, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    report(release.commit_needs_ci(folder, "HEAD"), "병합 커밋이 들여온 파일도 CI 경로로 맞춘다")

    with open(os.path.join(folder, "README.md"), "w") as handle:
        handle.write("y\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "docs")
    report(not release.commit_needs_ci(folder, "HEAD"), "CI 경로 밖만 바꾼 커밋은 CI 가 돌지 않는다")

# --- 기다리는 시간 환경 변수가 숫자가 아니어도 다른 하위 명령은 돈다
environment = dict(os.environ, PLUGIN_RELEASE_CI_WAIT_SECONDS="abc")
finished = subprocess.run([sys.executable, RELEASE, "--help"], capture_output=True, text=True, env=environment)
report(finished.returncode == 0, "기다리는 시간 환경 변수가 잘못돼도 스크립트는 시작된다")

sys.exit(1 if failures else 0)
