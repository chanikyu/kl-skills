"""readable-code — Python 이 아닌 언어에서 이름과 함수 자리를 찾는다.

Python 은 내장 분석기(ast)로 읽는다. 다른 언어마다 분석기를 들이면 쓰는 사람마다 설치할
것이 늘어나므로, 언어마다 주석·문자열의 모양과 "변수·함수·타입 선언"의 정규식을
data/languages.json 에 적어 두고 여기서는 그것을 맞춰 보기만 한다(2026-11-18 사용자 결정:
규칙 파일 + 패턴). 언어를 더하거나 패턴을 고칠 때는 그 파일을 고치고, 이 코드는 고치지 않는다.

정규식은 문법을 다 알지 못한다. 그래서
  1. 주석과 문자열을 먼저 공백으로 지운다. 그 속 글자를 이름으로 잡지 않으려는 것이다.
  2. 함수 본문은 중괄호를 세서 찾는다. end 로 닫는 언어(Ruby·Lua·Julia·Elixir)는 본문을
     찾지 않고 이름만 본다.
틀릴 수 있으므로 이 결과는 알리기만 하고 막지 않는다. 판정(어떤 이름이 나쁜가)은
check_code.py 가 Python 과 같은 기준으로 한다. 여기는 찾기만 한다.
"""

import bisect
import json
import os
import re
from collections import namedtuple

# 함수·타입 하나: 종류, 이름, 선언 줄, 본문 줄 수, 위에 설명 주석이 있나, 본문 안에 주석이 있나
Block = namedtuple("Block", "kind name line body_lines has_doc has_comment_inside")
# 파일 하나를 읽은 결과: 이름 -> 처음 나온 줄, 블록들, 맨 위가 설명 주석인가
Parsed = namedtuple("Parsed", "names blocks has_header_comment")

DECLARATION_KINDS = ("variables", "functions", "types")
# 셸 heredoc 의 시작 "<<끝표시", "<<-'끝표시'". "<<<"(here-string)는 따로 거른다.
HEREDOC_START = re.compile(r"<<-?[ \t]*(['\"]?)([A-Za-z_]\w*)\1")
# 여는 중괄호가 다음 줄 맨 앞에 오는 모양(Allman 방식)까지만 본문으로 인정한다. 더 멀리
# 찾으면 본문 없는 선언(인터페이스 메서드)에 다음 함수의 본문을 붙이게 된다.
NEXT_LINE_BRACE = re.compile(r"\n[ \t]*\{")
# 짧은 문자 상수 'a', '\n', '\u{1F600}'. Rust 의 수명 표시 'a 와 가르려고 닫는 따옴표까지 본다.
CHAR_LITERAL = re.compile(r"'(?:\\[^'\n]{1,10}|[^'\\\n])'")
# 파일 맨 위 설명을 찾을 때 건너뛰는 줄. 실행기 지정(#!)과 PHP 여는 표시는 설명 자리가 아니다.
HEADER_SKIP_PREFIXES = ("#!", "<?php")


def load_languages(data_dir):
    """규칙 파일을 읽어 확장자 -> 언어 규칙으로 준다. 파일이 없거나 깨졌으면 빈 사전.

    규칙 파일이 사라졌다고 Python 검사까지 멈추는 것보다, 다른 언어 검사만 빠지는 쪽이
    덜 해롭다(check_code.load_names 와 같은 판단). 정규식이 틀렸으면 그대로 터지게 둔다 —
    조용히 빠지면 그 언어가 검사되지 않는 줄 아무도 모른다.
    """
    try:
        with open(os.path.join(data_dir, "languages.json"), encoding="utf-8") as handle:
            entries = json.load(handle).get("languages", [])
    except (OSError, ValueError):
        return {}
    by_extension = {}
    for entry in entries:
        # 파일을 읽을 때마다 정규식을 새로 만들지 않도록 여기서 한 번 컴파일해 둔다.
        compiled = dict(entry)
        for kind in DECLARATION_KINDS:
            compiled[kind] = [re.compile(pattern) for pattern in entry.get(kind, [])]
        compiled["keywords"] = frozenset(entry.get("keywords", []))
        for extension in entry.get("extensions", []):
            by_extension[extension.lower()] = compiled
    return by_extension


def language_for(path, languages):
    """확장자로 언어 규칙을 고른다. 모르는 확장자면 None."""
    return languages.get(os.path.splitext(path)[1].lower())


def _line_starts(text):
    """줄마다 시작하는 글자 자리. 자리 -> 줄 번호를 이분 탐색으로 바꾸려고 둔다."""
    return [0] + [index + 1 for index, letter in enumerate(text) if letter == "\n"]


def _line_of(line_starts, offset):
    """글자 자리가 몇 번째 줄인가(1부터)."""
    return bisect.bisect_right(line_starts, offset)


def _line_end(text, start):
    """start 가 있는 줄의 줄바꿈 자리. 마지막 줄이면 글 끝."""
    found = text.find("\n", start)
    return len(text) if found < 0 else found


def _find_end(text, start, closer):
    """closer 가 끝나는 자리. 닫히지 않았으면 글 끝."""
    found = text.find(closer, start)
    return len(text) if found < 0 else found + len(closer)


def _string_end(text, start, lang, multiline):
    """start 의 따옴표로 시작한 문자열이 끝나는 자리.

    한 줄짜리 문자열은 줄이 끝나면 닫힌 것으로 본다. 따옴표 하나를 잘못 읽어도 파일 끝까지
    코드가 지워지지 않게 하려는 것이다.
    """
    quote = text[start]
    escape = None if quote in lang.get("raw_quotes", []) else lang.get("escape", "\\")
    index = start + 1
    while index < len(text):
        current_char = text[index]
        if escape and current_char == escape:
            index += 2
            continue
        if current_char == quote:
            return index + 1
        if current_char == "\n" and not multiline:
            return index
        index += 1
    return len(text)


def _comment_allowed(text, start, lang):
    """이 자리의 주석 표시가 정말 주석인가. 셸의 ${#arr} 나 $# 의 # 는 주석이 아니다."""
    if not lang.get("comment_needs_space"):
        return True
    return start == 0 or text[start - 1] in " \t\n;|&("


def _skipped_span(text, start, lang):
    """start 에서 주석이나 문자열이 시작하면 (끝 자리, 주석인가). 아니면 None.

    블록 주석을 줄 주석보다 먼저 본다. Lua 의 --[[ 는 -- 로도 시작하기 때문이다.
    """
    # Ruby 의 =begin, Perl 의 =pod 는 줄 맨 앞에서만 주석이다. 식 안의 "=begin" 은 아니다.
    at_line_start = start == 0 or text[start - 1] == "\n"
    for opener, closer in lang.get("block_comments", []):
        if lang.get("line_start_blocks") and not at_line_start:
            continue
        if text.startswith(opener, start):
            return _find_end(text, start + len(opener), closer), True
    for marker in lang.get("line_comments", []):
        if text.startswith(marker, start) and _comment_allowed(text, start, lang):
            return _line_end(text, start), True
    # """ 같은 긴 문자열은 따옴표 하나짜리보다 먼저 본다. 아니면 "" 와 " 로 잘못 쪼갠다.
    for opener, closer in lang.get("long_strings", []):
        if text.startswith(opener, start):
            return _find_end(text, start + len(opener), closer), False
    first_char = text[start]
    if first_char in lang.get("strings", []):
        return _string_end(text, start, lang, multiline=False), False
    if first_char in lang.get("multiline_strings", []):
        return _string_end(text, start, lang, multiline=True), False
    # 문자 상수는 닫는 따옴표가 바로 뒤에 있을 때만 문자열로 본다(Rust 수명 'a 는 아니다).
    if first_char == "'" and lang.get("char_literal"):
        match = CHAR_LITERAL.match(text, start)
        if match:
            return match.end(), False
    return None


def _blank(chars, start, end):
    """chars[start:end] 를 공백으로 바꾼다. 줄바꿈은 남겨 줄 번호를 지킨다."""
    for index in range(start, end):
        if chars[index] != "\n":
            chars[index] = " "


def _blank_heredocs(text, chars, start, end_marks):
    """셸 heredoc 본문을 지우고 그 다음 자리를 준다. 본문은 글이지 코드가 아니다."""
    index = start
    for end_mark in end_marks:
        while index < len(text):
            line_end = _line_end(text, index)
            line_text = text[index:line_end]
            _blank(chars, index, line_end)
            index = line_end + 1
            if line_text.strip() == end_mark:
                break
    return index


def blank_out(text, lang):
    """주석과 문자열을 공백으로 바꾼 코드와, 주석이 있는 줄 번호들을 준다.

    줄바꿈은 그대로 둬서 줄 번호가 원본과 같다. 문자열 속 "{" 나 "let x" 를 코드로 읽지
    않으려는 것이다.
    """
    chars = list(text)
    line_starts = _line_starts(text)
    comment_lines = set()
    pending_heredocs = []
    index = 0
    while index < len(text):
        # heredoc 본문은 그 표시가 나온 줄이 끝난 다음 줄부터 시작한다.
        if text[index] == "\n":
            index += 1
            if pending_heredocs:
                index = _blank_heredocs(text, chars, index, pending_heredocs)
                pending_heredocs = []
            continue
        span = _skipped_span(text, index, lang)
        if span:
            end, is_comment = span
            if is_comment:
                first, last = _line_of(line_starts, index), _line_of(line_starts, max(end - 1, index))
                comment_lines.update(range(first, last + 1))
            _blank(chars, index, end)
            index = max(end, index + 1)
            continue
        if lang.get("heredoc") and text.startswith("<<", index) and not text.startswith("<<<", index):
            match = HEREDOC_START.match(text, index)
            if match:
                pending_heredocs.append(match.group(2))
                index = match.end()
                continue
        index += 1
    return "".join(chars), comment_lines


def _pairs(code):
    """여는 괄호 자리 -> 닫는 괄호 바로 뒤 자리. 한 번 훑어 모든 짝을 미리 찾아 둔다.

    함수마다 닫는 괄호를 새로 찾으면 큰 파일에서 함수 수 × 파일 길이만큼 돈다.
    """
    pairs, stacks = {}, {"(": [], "{": []}
    openers = {")": "(", "}": "{"}
    for index, bracket in enumerate(code):
        if bracket in stacks:
            stacks[bracket].append(index)
        elif bracket in openers and stacks[openers[bracket]]:
            pairs[stacks[openers[bracket]].pop()] = index + 1
    return pairs


def _body_span(code, name_at, pairs, line_starts):
    """이름 다음에 오는 { ... } 본문의 (여는 줄, 닫는 줄). 본문이 없으면 None.

    인자 목록 괄호가 있으면 닫힐 때까지 넘기고, 그 줄에서 ; 보다 먼저 { 가 오거나 바로
    다음 줄 맨 앞이 { 이면 본문으로 본다. Go 의 받는 쪽 (r *T) 는 이름보다 앞이라 걸리지 않는다.
    """
    line_end = _line_end(code, name_at)
    paren, brace = code.find("(", name_at, line_end), code.find("{", name_at, line_end)
    position = name_at
    # 인자 목록이 여러 줄이어도 닫는 괄호까지 한 번에 넘긴다.
    if paren >= 0 and (brace < 0 or paren < brace):
        position = pairs.get(paren)
        if position is None:
            return None
    line_end = _line_end(code, position)
    rest = code[position:line_end]
    # ; 가 먼저 오면 본문 없는 선언(C 의 함수 원형, Rust 의 struct X;)이다.
    brace, semicolon = rest.find("{"), rest.find(";")
    if brace >= 0 and (semicolon < 0 or brace < semicolon):
        open_at = position + brace
    elif semicolon < 0 and NEXT_LINE_BRACE.match(code, line_end):
        open_at = code.index("{", line_end)
    else:
        return None
    close_after = pairs.get(open_at)
    if close_after is None:
        return None
    return _line_of(line_starts, open_at), _line_of(line_starts, close_after - 1)


def _has_doc_above(lineno, raw_lines, comment_only, lang):
    """선언 바로 위(장식·속성 줄은 건너뛴다)가 주석만 있는 줄인가.

    /** */, ///, #' 처럼 언어마다 설명 주석 모양이 다르지만, 바로 위에 주석이 붙어 있으면
    설명으로 본다. 모양까지 따지면 언어마다 규칙이 늘고, 막는 검사가 아니라 알리는 검사다.
    """
    prefixes = tuple(lang.get("attributes", []))
    above = lineno - 1
    while prefixes and above >= 1 and raw_lines[above - 1].strip().startswith(prefixes):
        above -= 1
    return above in comment_only


def _has_header_comment(raw_lines, comment_only):
    """파일 맨 위(실행기 지정 줄 다음)가 주석인가. 빈 파일은 지적하지 않는다."""
    for number, line_text in enumerate(raw_lines, 1):
        stripped = line_text.strip()
        if not stripped or stripped.startswith(HEADER_SKIP_PREFIXES):
            continue
        return number in comment_only
    return True


def _declarations(code_lines, lang):
    """(종류, 이름, 줄 번호, 그 줄 안의 이름 자리) 를 선언마다 하나씩 낸다."""
    for lineno, line_text in enumerate(code_lines, 1):
        for kind in DECLARATION_KINDS:
            for pattern in lang[kind]:
                for match in pattern.finditer(line_text):
                    name = match.group("name")
                    if name and name not in lang["keywords"]:
                        yield kind, name, lineno, match.start("name")


def parse(text, lang):
    """이름이 처음 나온 줄, 함수·타입 블록, 파일 맨 위 설명 여부를 찾는다."""
    code, comment_lines = blank_out(text, lang)
    code_lines, raw_lines = code.split("\n"), text.split("\n")
    comment_only = {number for number in comment_lines if not code_lines[number - 1].strip()}
    line_starts, pairs = _line_starts(code), _pairs(code)
    has_braces = lang.get("body") == "braces"
    names, blocks, seen = {}, [], set()
    for kind, name, lineno, column in _declarations(code_lines, lang):
        names.setdefault(name, lineno)
        # 변수에는 본문이 없다. 같은 선언을 패턴 두 개가 잡을 수 있어 한 번만 센다.
        if kind == "variables" or not has_braces or (kind, name, lineno) in seen:
            continue
        seen.add((kind, name, lineno))
        span = _body_span(code, line_starts[lineno - 1] + column, pairs, line_starts)
        if span is None:
            continue
        open_line, close_line = span
        inside = any(open_line <= number <= close_line for number in comment_lines)
        blocks.append(Block(kind, name, lineno, max(close_line - open_line - 1, 0),
                            _has_doc_above(lineno, raw_lines, comment_only, lang), inside))
    return Parsed(names, blocks, _has_header_comment(raw_lines, comment_only))
