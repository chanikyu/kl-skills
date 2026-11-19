#!/usr/bin/env python3
"""no-hardcoding — 코드에 박힌 값 가운데 기계로 확실히 가려지는 두 가지만 본다.

    check_hardcoding.py [--changed] [--exit-zero] [--limit N] [--max-items N] FILE [FILE...]

  absolute-path   이 기계에서만 맞는 절대경로 (/Users/이름, /home/이름, C:\\ 같은 것) — H3
  long-literal    값만 늘어놓은 사전·집합·목록·튜플이 항목 5개를 넘는다 — 데이터 파일로 뺄 자리, H2

임계값 숫자(0.05 같은 것)는 보지 않는다. 물리상수·규격값처럼 코드에 둬도 되는 숫자(H5)와
기계로 가를 수 없어서, 잡으면 대부분이 잘못 잡은 것이 된다. 그건 SKILL.md 의 H4 로 남긴다.

파이썬만 본다. 들어 있는 분석기(ast)로 읽으므로 주석과 설명문 속 예시 경로는 잡지 않는다.
어떤 경로를 '이 기계에서만 맞는 경로' 로 볼지는 data/machine-paths.txt 를 고친다.
"""

import argparse
import ast
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
MACHINE_PATHS = os.path.join(HERE, "..", "data", "machine-paths.txt")
# 마지막 커밋의 내용을 꺼내는 일은 readable-code 검사기와 같다. 두 벌로 두면 둘이 먼저 어긋난다.
sys.path.insert(0, os.path.join(HERE, "..", "..", "readable-code", "scripts"))
from check_code import committed_source  # noqa: E402

# SKILL.md H2 "항목이 5개를 넘어가는 사전·목록은 거의 항상 데이터다" 의 5.
MAX_ITEMS_DEFAULT = 5
# 경로가 이 글자들 뒤에서 시작할 때만 잡는다. 주소 한가운데의 /home/ 을 경로로 읽지 않으려는 것이다.
PATH_START = r"(?:^|(?<=[\s\"'=(,]))"
# 이 함수에 바로 넘긴 목록은 이름 붙은 표와 같다: frozenset({...}). 그 밖의 호출에 바로 넘긴
# 목록(subprocess.run([...]) 의 명령 줄, endswith((...)) 의 후보)은 표가 아니라 그 호출의 인자다.
CONTAINER_CALLS = {"set", "frozenset", "tuple", "list", "dict"}
CONTAINERS = (ast.Dict, ast.Set, ast.List, ast.Tuple)
# 3.6·3.7 의 ast 는 상수를 Str·Num 같은 따로 된 노드로 준다. 3.8 부터는 모두 Constant 이고,
# 옛 이름은 3.12 부터 쓸 때마다 경고를 내다가 3.14 에서 없어졌다. 그래서 옛 판에서만 찾는다.
OLD_AST = sys.version_info < (3, 8)


def load_path_patterns(path=MACHINE_PATHS):
    """기준 파일의 정규식들을 하나로 묶는다. 파일이 없으면 None — 경로 검사만 조용히 빠진다."""
    patterns = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    except OSError:
        return None
    if not patterns:
        return None
    return re.compile(PATH_START + "(?:" + "|".join(patterns) + ")")


def string_value(node):
    """문자열 상수면 그 글을, 아니면 None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if OLD_AST and isinstance(node, ast.Str):
        return node.s
    return None


def is_plain_value(node):
    """글자·숫자·참거짓·None 처럼 계산 없이 적힌 값인가. -1 같은 음수도 값으로 본다."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        node = node.operand
    if isinstance(node, ast.Constant):
        return True
    return OLD_AST and isinstance(node, (ast.Str, ast.Num, ast.Bytes, ast.NameConstant))


def widest_plain(node):
    """값만으로 된 묶음이면 그 안에서 가장 긴 묶음의 항목 수, 하나라도 계산이 섞이면 None.

    표가 표 안에 들어 있는 꼴(행 10개짜리 2차원 표, 목록을 값으로 가진 사전)도 하나의 표로 본다.
    """
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):   # {**other} 는 다른 사전을 펼친 것이다
            return None
        parts, width = list(node.keys) + list(node.values), len(node.keys)
    elif isinstance(node, CONTAINERS):
        parts, width = node.elts, len(node.elts)
    else:
        return 0 if is_plain_value(node) else None
    for part in parts:
        inner = widest_plain(part)
        if inner is None:
            return None
        width = max(width, inner)
    return width


def docstring_nodes(tree):
    """모듈·클래스·함수의 설명문 노드들. 설명문 속 예시 경로는 실행되는 값이 아니다."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and string_value(body[0].value) is not None:
                found.add(id(body[0].value))
    return found


def call_name(call):
    """호출한 함수의 이름. foo(...) 는 foo, mod.foo(...) 는 foo."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def table_name(node, parent):
    """표가 이름에 담겼으면 그 이름. NAME = [...] 와 NAME: list = [...] 만 본다."""
    if isinstance(parent, ast.Assign) and len(parent.targets) == 1 and isinstance(parent.targets[0], ast.Name):
        return parent.targets[0].id
    if isinstance(parent, ast.AnnAssign) and isinstance(parent.target, ast.Name):
        return parent.target.id
    return None


def is_own_vocabulary(node, string_counts):
    """표의 글자 값 절반 이상이 같은 파일의 다른 자리에도 나오는가.

    그렇다면 그 표는 바깥에서 온 데이터가 아니라 코드가 스스로 쓰는 낱말 목록이다 — CSV 열 이름
    ["turn", "fired", ...] 이나 검사 이름 ("not-indexed", ...) 처럼 코드가 그 낱말로 행을 만들고
    지적을 낸다. H2 의 물음 "이 값이 바뀌면 로직도 바뀌는가" 에 '그렇다' 인 경우다(2026-11-19,
    이 저장소의 코드 36개에 돌려 잡힌 5건 중 3건이 이 꼴이었다).
    """
    inside = Counter(text for text in (string_value(part) for part in ast.walk(node)) if text is not None)
    if not inside:
        return False
    reused = sum(1 for text in inside if string_counts[text] > inside[text])
    return reused * 2 >= len(inside)


def check(path, source, path_pattern, max_items):
    """한 파일의 지적 목록. 지적마다 key 를 단다 — 마지막 커밋에 이미 있던 것을 가를 때 쓴다."""
    found = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return found   # 구문 오류는 readable-code 검사기가 알린다. 같은 말을 두 번 하지 않는다.

    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    docstrings = docstring_nodes(tree)
    string_counts = Counter(text for text in (string_value(node) for node in ast.walk(tree)) if text is not None)

    for node in ast.walk(tree):
        text = string_value(node)
        if text is not None and path_pattern is not None and id(node) not in docstrings:
            hit = path_pattern.search(text)
            if hit:
                found.append({"path": path, "line": node.lineno, "code": "absolute-path", "key": text,
                              "msg": "'%s' 에 이 기계에서만 맞는 경로(%s)가 들어 있다"
                                     % (text.strip()[:80], hit.group(0)),
                              "fix": "스크립트 위치에서 계산하거나(__file__) 인자·환경변수로 받는다 (H3)"})
            continue
        if not isinstance(node, CONTAINERS) or isinstance(getattr(node, "ctx", None), ast.Store):
            continue
        parent = parents.get(id(node))
        if isinstance(parent, CONTAINERS):
            continue   # 바깥 표에서 한 번에 판정한다
        if isinstance(parent, ast.keyword):
            parent = parents.get(id(parent))
        if isinstance(parent, ast.Call) and call_name(parent) not in CONTAINER_CALLS:
            continue
        if isinstance(parent, ast.Call):
            parent = parents.get(id(parent))   # frozenset({...}) 는 그 바깥의 NAME = 로 이름을 찾는다
        width = widest_plain(node)
        if width is None or width <= max_items or is_own_vocabulary(node, string_counts):
            continue
        name = table_name(node, parent)
        if name and name.startswith("__") and name.endswith("__"):
            continue   # __all__ 같은 이름은 파이썬이 그 자리에 목록을 요구한다
        label = "'%s' 에 " % name if name else ""
        found.append({"path": path, "line": node.lineno, "code": "long-literal",
                      "key": name or ast.dump(node),
                      "msg": "%s값 %d개짜리 표를 코드에 늘어놓았다" % (label, width),
                      "fix": "그 값이 이미 있는 파일이 있으면 그것을 읽고, 없으면 옆에 .tsv/.json 으로 빼서 읽는다 (H1·H2)"})
    return found


def main(argv=None):
    """명령줄 입구. 찾은 것이 있으면 1로 끝낸다. 훅은 --exit-zero 를 준다 — 알리기만 한다."""
    parser = argparse.ArgumentParser(description="파이썬 코드에 박힌 절대경로와 긴 값 목록을 찾는다.")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--max-items", type=int, default=MAX_ITEMS_DEFAULT,
                        help="값만 늘어놓은 묶음이 이 개수를 넘으면 알린다 (기본 %d)" % MAX_ITEMS_DEFAULT)
    parser.add_argument("--limit", type=int, default=0, help="이 개수까지만 출력(0=전부)")
    parser.add_argument("--exit-zero", action="store_true", help="찾아도 0으로 끝낸다(훅용)")
    parser.add_argument("--changed", action="store_true",
                        help="git 저장소의 파일이면 마지막 커밋에 없던 값만 지적한다")
    cfg = parser.parse_args(argv)

    path_pattern = load_path_patterns()
    found, narrowed_count = [], 0
    for path in cfg.files:
        if not path.endswith(".py"):
            continue
        try:
            source = open(path, encoding="utf-8", errors="replace").read()
        except OSError as err:
            print("읽을 수 없다: %s (%s)" % (path, err), file=sys.stderr)
            continue
        file_found = check(path, source, path_pattern, cfg.max_items)
        old_source = committed_source(path) if cfg.changed else None
        if old_source is not None:
            # 옛 표에 항목 하나를 더했다고 그 표 전체를 지적하면 손대지 않은 것을 "김에" 고치게 된다.
            narrowed_count += 1
            old_keys = {finding["key"] for finding in check(path, old_source, path_pattern, cfg.max_items)}
            file_found = [finding for finding in file_found if finding["key"] not in old_keys]
        found += file_found

    show = sorted(found, key=lambda finding: (finding["path"], finding["line"]))
    rest = 0
    if cfg.limit and len(show) > cfg.limit:
        rest, show = len(show) - cfg.limit, show[:cfg.limit]
    for finding in show:
        print("%s:%d [%s] %s" % (finding["path"], finding["line"], finding["code"], finding["msg"]))
        print("    고친 예: %s" % finding["fix"])
    if rest:
        print("... 그리고 %d건 더 (--limit 를 올려서 전부 본다)" % rest)
    files_text = "파일 %d개" % len(cfg.files)
    if narrowed_count:
        files_text += ", 그중 %d개는 마지막 커밋에 없던 값만 봤다" % narrowed_count
    print("no-hardcoding: 경고 %d건 — %s" % (len(found), files_text))
    return 0 if (cfg.exit_zero or not found) else 1


if __name__ == "__main__":
    sys.exit(main())
