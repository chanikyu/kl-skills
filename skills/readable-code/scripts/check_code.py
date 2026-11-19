#!/usr/bin/env python3
"""readable-code — 코드에서 기계로 확인되는 두 가지만 본다.

    check_code.py [--all] [--limit N] FILE [FILE...]

보는 것은 **이름**과 **설명**이다. 둘 다 "나중에 이 코드를 읽는 사람"이 걸리는 자리다.

  vague-name                무엇인지 알 수 없는 이름 (a, s, tmp, data)
  no-docstring              여러 줄짜리 함수·클래스에 설명문이 없다
  uncommented-long-function 긴 함수 안에 주석이 한 줄도 없다
  no-module-docstring       파일이 무엇을 하는 파일인지 맨 위에 안 적혀 있다

파이썬은 들어 있는 분석기(ast)로 구문을 그대로 읽으므로, 문자열이나 주석 안의 글자를
변수로 착각하지 않는다. 주석 위치는 tokenize 로 얻는다 — `"# 이건 문자열"` 을 주석으로
세지 않기 위해서다.

다른 언어(JavaScript·TypeScript·Rust·Swift·Go·셸 등, 목록은 data/languages.json)는
other_languages.py 가 규칙 파일의 패턴으로 이름과 함수 자리를 찾고, 판정은 여기서 파이썬과
같은 기준으로 한다. 패턴이라 드물게 잘못 잡을 수 있다.

판정 기준은 전부 `data/` 의 파일에서 읽는다. 어떤 짧은 이름을 허용할지, 어떤 긴 이름을
모호하다고 볼지는 그 파일을 고친다. 코드를 고치지 않는다.

**값을 코드에 박는 문제는 여기서 보지 않는다.** 그건 `no-hardcoding` 스킬의 검사기
(check_hardcoding.py)가 보고, 같은 훅(code-check)이 둘을 함께 부른다. 같은 규칙을 두 곳에
두면 그 둘이 먼저 어긋난다.
"""

import argparse
import ast
import io
import os
import subprocess
import sys
import tokenize

import other_languages

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


def committed_source(path):
    """마지막 커밋에 들어 있던 이 파일의 내용. 없으면 None.

    git 이 없거나, 저장소 밖이거나, 아직 커밋한 적 없는 파일이면 None 이다. 그런 파일은
    통째로 새로 쓴 것이라 전부 검사하는 게 맞다. --no-textconv 는 사용자가 걸어 둔 변환
    도구 대신 저장된 내용 그대로를 받으려는 것이다.
    """
    folder, name = os.path.split(os.path.abspath(path))
    try:
        shown = subprocess.run(["git", "-C", folder, "show", "--no-textconv", "HEAD:./" + name],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    if shown.returncode != 0:
        return None
    return shown.stdout.decode("utf-8", "replace")


def old_names_in(old_source, lang):
    """마지막 커밋 때 파일에 있던 이름들. 옛 파일을 읽지 못하면 None.

    lang 이 None 이면 파이썬이다. 옛 파일이 깨져 있으면 비교할 이름이 없으므로 None 을
    줘서 전부 남기게 한다.
    """
    if lang is not None:
        return set(other_languages.parse(old_source, lang).names)
    try:
        return set(stored_names(ast.parse(old_source)))
    except SyntaxError:
        return None


def drop_old_names(findings, old_names):
    """마지막 커밋에 이미 있던 이름에 대한 지적을 뺀다.

    줄이 아니라 이름으로 가르는 까닭: 옛 이름 `s` 가 처음 나오는 줄을 고치면 그 줄은
    "바뀐 줄"이 되어 `s` 를 지적하고, 함수 전체의 `s` 를 바꾸라고 부추긴다. 기존 함수의
    def 줄에 인자 하나를 더해도 그 함수의 빠진 설명문을 지적하게 된다(2026-11-18 재현).
    둘 다 손대지 않은 것을 "김에" 고치게 만든다. 구문 오류는 이름과 상관없이 남긴다 —
    숨기면 "깨끗하다"로 읽힌다.
    """
    if old_names is None:
        return findings
    kept = []
    for finding in findings:
        if finding["code"] == "no-module-docstring":
            continue   # 파일이 이미 있었으니 맨 위 설명문도 옛것이다
        if finding["code"] != "syntax-error" and finding["name"] in old_names:
            continue
        kept.append(finding)
    return kept


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


def judge_name(add, name, lineno, short_ok, vague):
    """이름 하나를 기준에 맞춰 보고, 걸리면 add 로 지적을 남긴다.

    파이썬과 다른 언어가 같이 쓴다. 기준을 두 곳에 두면 그 둘이 먼저 어긋난다.
    """
    low = name.lower().strip("_")
    if len(name.strip("_")) <= 2 and name not in short_ok:
        add(lineno, "warn", "vague-name",
            "이름 '%s' 로는 무엇을 담았는지 알 수 없다" % name,
            "담긴 것을 그대로 쓴다: s -> text, p -> path, df -> samples", name)
    elif low in vague:
        add(lineno, "warn", "vague-name",
            "이름 '%s' 는 길지만 무엇인지 안 알려준다" % name,
            "'무엇의' 를 붙인다: data -> allele_counts, tmp -> merged_rows", name)


def check_other(path, source, lang, cfg, short_ok, vague):
    """파이썬이 아닌 파일 하나를 검사해 찾은 것들의 목록을 준다.

    이름과 함수 자리는 other_languages 가 규칙 파일의 패턴으로 찾고, 판정은 파이썬과 같다.
    설명문은 함수 바로 위의 주석(/** */, ///, #' 등)이다. 중괄호를 쓰지 않는 언어는
    블록을 찾지 않으므로 이름만 본다.
    """
    found = []

    def add(line, sev, code, msg, fix="", name=None):
        found.append({"path": path, "line": line, "sev": sev, "code": code,
                      "msg": msg, "fix": fix, "name": name})

    parsed = other_languages.parse(source, lang)
    # 메시지와 등급은 파이썬 쪽 check() 와 같게 둔다. 언어가 달라도 같은 지적은 같게 읽혀야 한다.
    if not parsed.has_header_comment:
        add(1, "note", "no-module-docstring",
            "이 파일이 무엇을 하는 파일인지 맨 위에 안 적혀 있다",
            "파일 첫머리에 무엇을 하는 파일인지 주석 한 줄을 둔다")
    for name, lineno in sorted(parsed.names.items(), key=lambda kv: kv[1]):
        judge_name(add, name, lineno, short_ok, vague)
    for block in parsed.blocks:
        label = "함수" if block.kind == "functions" else "타입"
        if block.body_lines >= cfg.min_body and not block.has_doc:
            add(block.line, "warn", "no-docstring",
                "%s '%s' 가 %d줄인데 설명 주석이 없다" % (label, block.name, block.body_lines),
                "바로 위에 무엇을 하는지, 왜 이렇게 했는지 한두 줄 주석", block.name)
        if block.kind == "functions" and block.body_lines >= cfg.min_commented \
                and not block.has_comment_inside:
            add(block.line, "warn", "uncommented-long-function",
                "함수 '%s' 가 %d줄인데 안에 주석이 한 줄도 없다" % (block.name, block.body_lines),
                "판단이 들어간 자리마다 '왜 그렇게 했는지' 를 적는다", block.name)
    return found


def check(path, source, cfg, short_ok, vague):
    """한 파일을 검사해 찾은 것들의 목록을 준다.

    구문이 깨진 파일은 첫 항목으로 그 사실만 보고하고 끝낸다. 깨진 파일에서
    이름을 세는 것은 의미가 없고, 그 상태를 숨기면 "검사했는데 깨끗하다"로 읽힌다.
    """
    found = []

    def add(line, sev, code, msg, fix="", name=None):
        found.append({"path": path, "line": line, "sev": sev, "code": code,
                      "msg": msg, "fix": fix, "name": name})

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
        judge_name(add, name, lineno, short_ok, vague)

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
                "무엇을 하는지, 왜 이렇게 했는지 한두 줄", node.name)
        if isinstance(node, ast.ClassDef):
            continue
        last = max((getattr(child, "end_lineno", None) or child.lineno) for child in node.body)
        inside = [lineno for lineno in comments if node.lineno < lineno <= last]
        if span >= cfg.min_commented and not inside:
            add(node.lineno, "warn", "uncommented-long-function",
                "함수 '%s' 가 %d줄인데 안에 주석이 한 줄도 없다" % (node.name, span),
                "판단이 들어간 자리마다 '왜 그렇게 했는지' 를 적는다", node.name)

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
    parser.add_argument("--changed", action="store_true",
                        help="git 저장소의 파일이면 마지막 커밋에 없던 이름만 지적한다")
    cfg = parser.parse_args(argv)

    short_ok = load_names("short-names-ok.txt", cfg.data_dir)
    vague = set(name.lower() for name in load_names("vague-names.txt", cfg.data_dir))
    languages = other_languages.load_languages(cfg.data_dir or DATA_DIR)

    found = []
    narrowed_count = 0
    for path in cfg.files:
        # 파이썬이면 lang 은 None, 규칙 파일에 없는 확장자는 건너뛴다.
        lang = None if path.endswith(".py") else other_languages.language_for(path, languages)
        if lang is None and not path.endswith(".py"):
            continue
        try:
            source = open(path, encoding="utf-8", errors="replace").read()
        except OSError as err:
            print("읽을 수 없다: %s (%s)" % (path, err), file=sys.stderr)
            continue
        if lang is None:
            file_found = check(path, source, cfg, short_ok, vague)
        else:
            file_found = check_other(path, source, lang, cfg, short_ok, vague)
        old_source = committed_source(path) if cfg.changed else None
        if old_source is not None:
            narrowed_count += 1
            file_found = drop_old_names(file_found, old_names_in(old_source, lang))
        found += file_found

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
    files_text = "파일 %d개" % len(cfg.files)
    if narrowed_count:
        files_text += ", 그중 %d개는 마지막 커밋에 없던 이름만 봤다" % narrowed_count
    print("readable-code: %s — %s" % (tail, files_text))
    return 0 if (cfg.exit_zero or not warns) else 1


if __name__ == "__main__":
    sys.exit(main())
