#!/usr/bin/env python3
"""Claude Code 플러그인을 고친 뒤 설치본까지 반영하는 순서를, 건너뛸 수 없게 묶는다.

    release.py bump 0.19.0      버전을 plugin.json 과 version-files.txt 의 파일 모두에 쓴다
    release.py ship             푸시된 커밋의 CI 를 기다리고, 통과했을 때만 설치본을 바꾼다
    release.py verify           설치본의 버전과 훅이 살아 있는지 확인한다

고친 내용이 설치본에 닿기까지 조용히 끊기는 자리가 네 군데 있다(위키 plugin-update-flow):
버전을 안 올림 / 장터 복제본을 안 갱신함 / CI 가 끝나기 전에 설치함 / 세션을 다시 시작 안 함.
2026-11-11 에는 세 번째로 옛 바이너리가 설치본에 굳었다. 순서가 README 에만 있고 막는
장치가 없었기 때문이다. ship 은 CI 가 성공한 것을 확인하기 전에는 설치 명령을 부르지 않는다.

커밋과 푸시는 하지 않는다. 그건 사람이 허락할 일이라서, ship 은 푸시가 끝난 뒤에만 돈다.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

VERSION_FILES_LIST = "version-files.txt"      # 리포 뿌리. plugin.json 말고도 버전이 적힌 파일들
PLUGIN_MANIFEST = os.path.join(".claude-plugin", "plugin.json")
MARKETPLACE_MANIFEST = os.path.join(".claude-plugin", "marketplace.json")
# 설치 목록 위치. 테스트나 다른 설정 폴더를 쓸 때 환경 변수로 바꾼다.
INSTALLED_PLUGINS = os.environ.get("PLUGIN_RELEASE_INSTALLED_PLUGINS",
                                   os.path.expanduser("~/.claude/plugins/installed_plugins.json"))
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
CI_APPEAR_WAIT_SECONDS = 90   # 푸시 직후에는 CI 실행이 아직 목록에 없다. 이만큼 기다려 본다
CI_POLL_SECONDS = 5
BANNER_VERSION = re.compile(r"\bv(\d+\.\d+\.\d+)\b")


def run(command, cwd=None, check=True, timeout=None):
    """명령을 돌리고 (종료 코드, 출력)을 돌려준다. check 면 실패할 때 멈춘다."""
    finished = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    output = ((finished.stdout or "") + (finished.stderr or "")).strip()
    if check and finished.returncode != 0:
        raise SystemExit("실패: %s\n%s" % (" ".join(command), output))
    return finished.returncode, output


def repo_root(given):
    """리포 뿌리. 안 주면 지금 폴더가 든 git 저장소."""
    if given:
        return os.path.abspath(given)
    return run(["git", "rev-parse", "--show-toplevel"])[1]


def read_json(path):
    """JSON 파일을 읽는다."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def plugin_identity(root):
    """(플러그인 이름, 장터 이름, 지금 버전). 장터 파일이 없으면 장터 이름은 None."""
    manifest = read_json(os.path.join(root, PLUGIN_MANIFEST))
    market_path = os.path.join(root, MARKETPLACE_MANIFEST)
    market = read_json(market_path).get("name") if os.path.isfile(market_path) else None
    return manifest["name"], market, manifest["version"]


def version_files(root):
    """버전을 써야 할 파일들. plugin.json 은 늘 들어가고, 나머지는 version-files.txt 에서 읽는다."""
    files = [PLUGIN_MANIFEST]
    listed = os.path.join(root, VERSION_FILES_LIST)
    if os.path.isfile(listed):
        with open(listed, encoding="utf-8") as handle:
            files += [line.strip() for line in handle if line.strip() and not line.startswith("#")]
    return files


def bumped_text(path, new_version):
    """버전 줄만 바꾼 파일 내용을 돌려준다(쓰지는 않는다). 형식을 지키려고 그 줄만 고친다."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if path.endswith(".toml"):
        pattern = re.compile(r'^(version\s*=\s*")[^"]*(")', re.MULTILINE)
    else:
        pattern = re.compile(r'("version"\s*:\s*")[^"]*(")')
    changed, count = pattern.subn(lambda found: found.group(1) + new_version + found.group(2), text, count=1)
    if count != 1:
        raise SystemExit("버전 줄을 못 찾았다: %s — 아무 파일도 바꾸지 않았다" % path)
    return changed


def command_bump(options):
    """버전을 올린다. 지금보다 큰 X.Y.Z 만 받는다 — 같으면 업데이트가 아무것도 안 바꾼다."""
    root = repo_root(options.repo)
    _, _, current = plugin_identity(root)
    wanted = SEMVER.match(options.version)
    if not wanted:
        raise SystemExit("버전은 X.Y.Z 꼴이어야 한다: %s" % options.version)
    if tuple(map(int, wanted.groups())) <= tuple(map(int, SEMVER.match(current).groups())):
        raise SystemExit("새 버전 %s 가 지금 버전 %s 보다 커야 한다" % (options.version, current))
    # 모든 파일의 새 내용을 먼저 만들고, 하나라도 실패하면 아무것도 쓰지 않는다. 하나씩 쓰면
    # 중간에 멈췄을 때 plugin.json 만 올라가고, 다시 돌리면 "지금 버전보다 커야 한다" 로 막힌다.
    planned = [(relative_path, bumped_text(os.path.join(root, relative_path), options.version))
               for relative_path in version_files(root)]
    for relative_path, new_text in planned:
        with open(os.path.join(root, relative_path), "w", encoding="utf-8") as handle:
            handle.write(new_text)
        print("버전 %s → %s : %s" % (current, options.version, relative_path))
    return 0


def pushed_head(root):
    """작업 트리가 깨끗하고 HEAD 가 원격에 올라가 있으면 HEAD 커밋, 아니면 멈춘다."""
    if run(["git", "status", "--porcelain"], cwd=root)[1]:
        raise SystemExit("커밋 안 한 변경이 있다. 커밋하고 푸시한 뒤에 ship 한다")
    run(["git", "fetch", "-q"], cwd=root)
    head = run(["git", "rev-parse", "HEAD"], cwd=root)[1]
    code, upstream = run(["git", "rev-parse", "@{u}"], cwd=root, check=False)
    if code != 0 or upstream != head:
        raise SystemExit("HEAD 가 원격과 다르다 — 푸시하지 않았거나 원격에 새 커밋이 있다")
    return head


def find_ci_runs(root, commit):
    """그 커밋의 CI 실행 id 전부. 푸시 직후라 아직 없으면 잠깐씩 기다리며 다시 본다."""
    deadline = time.monotonic() + CI_APPEAR_WAIT_SECONDS
    while True:
        _, listing = run(["gh", "run", "list", "--commit", commit, "--json", "databaseId"], cwd=root)
        runs = json.loads(listing or "[]")
        if runs:
            return [entry["databaseId"] for entry in runs]
        if time.monotonic() > deadline:
            return []
        time.sleep(CI_POLL_SECONDS)


def command_ship(options):
    """CI 가 성공한 뒤에만 장터를 갱신하고 설치본을 바꾼다. 그다음 verify 를 돈다."""
    root = repo_root(options.repo)
    plugin, market, version = plugin_identity(root)
    if not market:
        raise SystemExit("%s 가 없다 — 장터 이름을 알 수 없다" % MARKETPLACE_MANIFEST)
    head = pushed_head(root)
    if options.no_ci:
        print("CI 확인을 건너뛴다(--no-ci). 이 리포에 CI 가 없을 때만 쓴다")
    else:
        run_ids = find_ci_runs(root, head)
        if not run_ids:
            raise SystemExit("커밋 %s 의 CI 실행이 %d초 안에 안 보인다. CI 가 없는 리포면 --no-ci"
                             % (head[:7], CI_APPEAR_WAIT_SECONDS))
        # 한 커밋에 워크플로가 여럿이면 전부 통과해야 한다. 첫 번째만 보면 실패한 둘째를 놓친다.
        for run_id in run_ids:
            print("CI %s 를 기다린다 (커밋 %s)" % (run_id, head[:7]))
            code, output = run(["gh", "run", "watch", str(run_id), "--exit-status"], cwd=root, check=False)
            if code != 0:
                # 여기서 멈추는 것이 이 스크립트의 핵심이다. 실패한 빌드를 설치하면 옛 바이너리가 굳는다.
                raise SystemExit("CI %s 가 실패했다 — 설치하지 않는다.\n%s" % (run_id, output[-1500:]))
        print("CI %d개 모두 통과" % len(run_ids))
        # CI 가 바이너리를 커밋했으면 그 커밋까지 받아야 장터 복제본과 같아진다.
        run(["git", "pull", "-q", "--rebase"], cwd=root)
    print(last_line(run(["claude", "plugin", "marketplace", "update", market], timeout=300)[1]))
    print(last_line(run(["claude", "plugin", "update", "%s@%s" % (plugin, market)], timeout=300)[1]))
    return verify(plugin, market, version)


def last_line(output):
    """명령 출력의 마지막 줄. 아무것도 안 찍는 명령도 있다 — 그때 멈추면 설치가 반쯤에서 끊긴다."""
    lines = output.splitlines()
    return lines[-1] if lines else "(출력 없음)"


def installed_copy(plugin, market):
    """세션이 실제로 쓰는 설치본 폴더. 장터 복제본이 아니라 installed_plugins.json 의 installPath 다."""
    try:
        entries = read_json(INSTALLED_PLUGINS)["plugins"]["%s@%s" % (plugin, market)]
    except (OSError, KeyError, ValueError):
        return None
    return entries[0]["installPath"] if entries else None


def hook_commands(install_path):
    """설치본 hooks.json 의 (사건, 명령, 제한 초) 목록. Windows 명령은 뺀다."""
    hooks_file = os.path.join(install_path, "hooks", "hooks.json")
    if not os.path.isfile(hooks_file):
        return []
    commands = []
    for event, groups in read_json(hooks_file).get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                if hook.get("type") == "command" and hook.get("command"):
                    commands.append((event, hook["command"], hook.get("timeout", 60)))
    return commands


def verify(plugin, market, expected_version):
    """설치본 버전이 맞고, 훅마다 빈 입력에 0으로 끝나는지 본다. 하나라도 틀리면 1."""
    install_path = installed_copy(plugin, market)
    if not install_path:
        print("설치본이 없다: %s@%s 가 %s 에 없다" % (plugin, market, INSTALLED_PLUGINS))
        return 1
    installed_version = read_json(os.path.join(install_path, PLUGIN_MANIFEST))["version"]
    problems = []
    if installed_version != expected_version:
        problems.append("설치본 버전 %s ≠ 리포 버전 %s" % (installed_version, expected_version))
    print("설치본: %s (버전 %s)" % (install_path, installed_version))
    environment = dict(os.environ, CLAUDE_PLUGIN_ROOT=install_path)
    # 빈 입력 {} 으로 부른다. 훅은 할 일이 없으면 조용히 0으로 끝나야 한다. 작업 폴더는 빈 임시 폴더.
    with tempfile.TemporaryDirectory() as empty_folder:
        for event, command, limit in hook_commands(install_path):
            shell_command = command.replace("${CLAUDE_PLUGIN_ROOT}", install_path)
            started = time.monotonic()
            try:
                finished = subprocess.run(["sh", "-c", shell_command], input="{}", capture_output=True,
                                          text=True, env=environment, cwd=empty_folder, timeout=limit)
                code, output = finished.returncode, (finished.stdout or "").strip()
            except subprocess.TimeoutExpired:
                code, output = "timeout", ""
            seconds = time.monotonic() - started
            name = shell_command.split()[-1]
            print("  %-18s %-17s 종료 %-7s %.2f초  %s" % (event, name, code, seconds, output[:70]))
            if code != 0:
                problems.append("%s 훅 %s 이 %s 로 끝났다" % (event, name, code))
            # 배너가 버전을 말하면 그것도 맞아야 한다. 설치본 버전은 맞는데 배너만 옛 것이면, 캐시에
            # 옛 바이너리가 굳은 것이다. 설치본 버전부터 다르면 그냥 아직 설치 안 된 것이라 따로 말하지 않는다.
            banner = BANNER_VERSION.search(output)
            if banner and banner.group(1) != expected_version and installed_version == expected_version:
                problems.append("배너 버전 v%s ≠ %s — 옛 바이너리가 굳었다. 지웠다 다시 설치한다"
                                % (banner.group(1), expected_version))
    for problem in problems:
        print("문제: " + problem)
    if not problems:
        print("설치본 확인 끝. 이 세션의 훅은 시작할 때 읽은 것이다 — 새 훅을 쓰려면 세션을 다시 시작한다")
    return 1 if problems else 0


def command_verify(options):
    """verify 만 따로 돈다. 세션을 다시 시작한 뒤의 확인에 쓴다."""
    plugin, market, version = plugin_identity(repo_root(options.repo))
    return verify(plugin, market, version)


def main(argv=None):
    """하위 명령을 고른다."""
    parser = argparse.ArgumentParser(description="플러그인 배포 순서를 지키게 한다")
    parser.add_argument("--repo", help="플러그인 리포 뿌리 (기본: 지금 폴더의 git 저장소)")
    commands = parser.add_subparsers(dest="command", required=True)
    bump = commands.add_parser("bump", help="버전을 모든 버전 파일에 쓴다")
    bump.add_argument("version", help="새 버전 X.Y.Z")
    bump.set_defaults(handler=command_bump)
    ship = commands.add_parser("ship", help="CI 통과를 확인한 뒤 설치본을 바꾸고 확인한다")
    ship.add_argument("--no-ci", action="store_true", help="CI 가 없는 리포에서만")
    ship.set_defaults(handler=command_ship)
    commands.add_parser("verify", help="설치본 버전과 훅을 확인한다").set_defaults(handler=command_verify)
    options = parser.parse_args(argv)
    return options.handler(options)


if __name__ == "__main__":
    sys.exit(main())
