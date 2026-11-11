#!/usr/bin/env python3
"""readable-code — 파이썬 코드에서 기계로 확인되는 두 가지만 본다.

    check_code.py [--all] [--limit N] FILE [FILE...]

보는 것은 **이름**과 **설명**이다. 둘 다 "나중에 이 코드를 읽는 사람"이 걸리는 자리다.

  vague-name                무엇인지 알 수 없는 이름 (a, s, tmp, data)
  no-docstring              여러 줄짜리 함수·클래스에 설명문이 없다
  uncommented-long-function 긴 함수 안에 주석이 한 줄도 없다
  no-module-docstring       파일이 무엇을 하는 파일인지 맨 위에 안 적혀 있다

파이썬에 들어 있는 분석기(ast)로 구문을 그대로 읽으므로, 문자열이나 주석 안의 글자를
변수로 착각하지 않는다. 주석 위치는 tokenize 로 얻는다 — `"# 이건 문자열"` 을 주석으로
세지 않기 위해서다.

판정 기준은 전부 `data/` 의 파일에서 읽는다. 어떤 짧은 이름을 허용할지, 어떤 긴 이름을
모호하다고 볼지는 그 파일을 고친다. 코드를 고치지 않는다.

**값을 코드에 박는 문제는 여기서 보지 않는다.** 그건 `no-hardcoding` 스킬이 담당하고,
절대경로는 훅이 이미 막는다. 같은 규칙을 두 곳에 두면 그 둘이 먼저 어긋난다.
"""

import argparse
import ast
import io
import os
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")


def load_names(filename, data_dir=None):
    """판정 기준 파일 한 장을 이름 집합으로 읽는다.

    파일이 없으면 빈 집합을 준다. 기준 파일이 사라졌다고 검사를 멈추는 것보다,
    그 검사만 조용히 빠지는 쪽이 덜 해롭다.
    """
    path = os.path.join(data_dir or DATA_DIR, filename)
    out = set()
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                out.add(line)
    except OSError:
        pass
    return out


def comment_lines(source):
    """주석이 실제로 있는 줄 번호. 문자열 안의 #은 세지 않는다."""
    lines = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                lines.add(token.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return lines


def stored_names(tree):
    """값이 담기는 쪽에 나오는 이름들을 (이름, 줄번호) 로. 처음 나온 자리만."""
    seen = {}

    def note(name, lineno):
        if isinstance(name, str) and name and name not in seen:
            seen[name] = lineno

    for node in ast.walk(tree):
        # 값이 들어가는 쪽(Store)만 본다. 읽는 쪽까지 세면 남이 만든 이름까지 지적한다.
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            note(node.id, node.lineno)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            note(node.name, node.lineno)
            # 인자도 읽는 사람이 보는 이름이다. 위치·키워드·*args·**kwargs 를 다 모은다.
            args = node.args
            every = list(getattr(args, "posonlyargs", [])) + list(args.args) + list(args.kwonlyargs)
            if args.vararg:
                every.append(args.vararg)
            if args.kwarg:
                every.append(args.kwarg)
            for arg in every:
                note(arg.arg, arg.lineno)
        elif isinstance(node, ast.ClassDef):
            note(node.name, node.lineno)
    return seen


def body_span(node):
    """본문이 몇 줄인가. 한 줄짜리 함수에 설명문을 요구하는 것은 과하다."""
    last = max((getattr(child, "end_lineno", None) or child.lineno)
               for child in node.body)
    return last - node.body[0].lineno + 1


def check(path, source, cfg, short_ok, vague):
    """한 파일을 검사해 찾은 것들의 목록을 준다.

    구문이 깨진 파일은 첫 항목으로 그 사실만 보고하고 끝낸다. 깨진 파일에서
    이름을 세는 것은 의미가 없고, 그 상태를 숨기면 "검사했는데 깨끗하다"로 읽힌다.
    """
    found = []

    def add(line, sev, code, msg, fix=""):
        found.append({"path": path, "line": line, "sev": sev, "code": code,
                      "msg": msg, "fix": fix})

    try:
        tree = ast.parse(source)
    except SyntaxError as err:
        add(err.lineno or 1, "warn", "syntax-error",
            "파이썬이 이 파일을 읽지 못한다: %s" % err.msg)
        return found

    # 파일 맨 위 설명문. 없으면 이 파일이 왜 있는지 아무 데도 안 적혀 있다는 뜻이다.
    if not ast.get_docstring(tree):
        add(1, "note", "no-module-docstring",
            "이 파일이 무엇을 하는 파일인지 맨 위에 안 적혀 있다",
            '파일 첫 줄에 """무엇을 하는 파일인지 한 줄""" 을 둔다')

    for name, lineno in sorted(stored_names(tree).items(), key=lambda kv: kv[1]):
        low = name.lower().strip("_")
        if len(name.strip("_")) <= 2 and name not in short_ok:
            add(lineno, "warn", "vague-name",
                "이름 '%s' 로는 무엇을 담았는지 알 수 없다" % name,
                "담긴 것을 그대로 쓴다: s -> text, p -> path, df -> samples")
        elif low in vague:
            add(lineno, "warn", "vague-name",
                "이름 '%s' 는 길지만 무엇인지 안 알려준다" % name,
                "'무엇의' 를 붙인다: data -> allele_counts, tmp -> merged_rows")

    # 설명문과 주석은 다른 것을 막는다. 설명문은 "무엇을 하는 함수인가"를,
    # 주석은 "이 자리에서 왜 이렇게 했나"를 남긴다. 그래서 둘을 따로 본다.
    comments = comment_lines(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not node.body:
            continue
        span = body_span(node)
        if span >= cfg.min_body and not ast.get_docstring(node):
            add(node.lineno, "warn", "no-docstring",
                "%s '%s' 가 %d줄인데 설명문이 없다" % (
                    "클래스" if isinstance(node, ast.ClassDef) else "함수", node.name, span),
                "무엇을 하는지, 왜 이렇게 했는지 한두 줄")
        if isinstance(node, ast.ClassDef):
            continue
        last = max((getattr(child, "end_lineno", None) or child.lineno) for child in node.body)
        inside = [lineno for lineno in comments if node.lineno < lineno <= last]
        if span >= cfg.min_commented and not inside:
            add(node.lineno, "warn", "uncommented-long-function",
                "함수 '%s' 가 %d줄인데 안에 주석이 한 줄도 없다" % (node.name, span),
                "판단이 들어간 자리마다 '왜 그렇게 했는지' 를 적는다")

    return found


def main(argv=None):
    """명령줄에서 불렸을 때의 입구. 찾은 것이 있으면 1로 끝낸다.

    훅에서 부를 때는 --exit-zero 를 준다. 훅이 0이 아닌 값을 돌려주면 작업이
    막히는데, 글이나 이름은 기계가 막을 대상이 아니라 알려 줄 대상이다.
    """
    parser = argparse.ArgumentParser(description="파이썬 코드의 이름과 설명을 검사한다.")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--all", action="store_true", help="참고 등급까지 보여준다")
    parser.add_argument("--limit", type=int, default=0, help="이 개수까지만 출력(0=전부)")
    parser.add_argument("--min-body", type=int, default=5,
                    help="설명문을 요구할 본문 줄 수 (기본 5)")
    parser.add_argument("--min-commented", type=int, default=20,
                    help="안에 주석을 요구할 본문 줄 수 (기본 20)")
    parser.add_argument("--data-dir", default=None, help="판정 기준 파일을 둔 디렉토리")
    parser.add_argument("--exit-zero", action="store_true", help="찾아도 0으로 끝낸다(훅용)")
    cfg = parser.parse_args(argv)

    short_ok = load_names("short-names-ok.txt", cfg.data_dir)
    vague = set(name.lower() for name in load_names("vague-names.txt", cfg.data_dir))

    found = []
    for path in cfg.files:
        if not path.endswith(".py"):
            continue
        try:
            source = open(path, encoding="utf-8", errors="replace").read()
        except OSError as err:
            print("읽을 수 없다: %s (%s)" % (path, err), file=sys.stderr)
            continue
        found += check(path, source, cfg, short_ok, vague)

    # 등급을 나눈다. 경고는 기본 출력, 참고는 --all 일 때만 — 참고 쪽은 일부러
    # 위양성을 감수한 검사라서 매번 보이면 잡음이 된다.
    warns = [finding for finding in found if finding["sev"] == "warn"]
    notes = [finding for finding in found if finding["sev"] != "warn"]
    show = sorted(warns + (notes if cfg.all else []), key=lambda f: (f["path"], f["line"]))
    rest = 0
    if cfg.limit and len(show) > cfg.limit:
        rest = len(show) - cfg.limit
        show = show[:cfg.limit]

    for finding in show:
        print("%s:%d [%s] %s" % (finding["path"], finding["line"],
                                 finding["code"], finding["msg"]))
        if finding["fix"]:
            print("    고친 예: %s" % finding["fix"])
    if rest:
        print("... 그리고 %d건 더 (--limit 를 올려서 전부 본다)" % rest)

    tail = "경고 %d건" % len(warns)
    if cfg.all:
        tail += ", 참고 %d건" % len(notes)
    elif notes:
        tail += " (참고 %d건은 --all 로 본다)" % len(notes)
    print("readable-code: %s — 파일 %d개" % (tail, len(cfg.files)))
    return 0 if (cfg.exit_zero or not warns) else 1


if __name__ == "__main__":
    sys.exit(main())
