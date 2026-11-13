#!/usr/bin/env python3
"""Find words a field does not use, and name the word it does use.

The word pairs live in data/domain-terms.tsv (wrong, right, field, source) — the one list,
never copied into code. Reads plain-text files and the text inside .pptx and .docx (both are
zip files of XML), so a slide deck is checked as itself, not only the script that built it.

Not counted as a use of a wrong word:
  - text inside backticks — a mention, for example when explaining the mistake
  - a line that carries IGNORE_MARK — tests and notes that must spell the wrong word
  - the glossary file itself

Usage: check_terms.py [--answer FILE] [--exit-zero] [--limit N] [PATH ...]
Prints one line per hit and a summary line; exits 1 when it found something (unless --exit-zero).
Asked for on 2026-11-13: slides used words the field and the person's own slides do not use.
"""

import argparse
import html
import os
import re
import sys
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
GLOSSARY = os.path.join(os.path.dirname(HERE), "data", "domain-terms.tsv")
IGNORE_MARK = "term-check: ok"
MAX_BYTES = 2_000_000        # 이보다 큰 글 파일은 결과물이라기보다 데이터다. 앞부분만 본다
BACKTICK_SPAN = re.compile(r"`[^`\n]*`")
XML_TAG = re.compile(r"<[^>]+>")
# 슬라이드·문서 안에서 문단이 끝나는 태그. 문단 사이는 줄을 바꿔야 "몇 번째 문단"을 알 수 있다
PARAGRAPH_END = re.compile(r"</(?:a|w):p>")
# 문단 안의 줄바꿈·탭 태그. 지우기만 하면 앞뒤 낱말이 붙어("두낱말") 용어를 못 찾는다 — 띄어쓰기로 바꾼다
INLINE_BREAK = re.compile(r"<(?:a:br|w:br|w:cr|w:tab)\b[^>]*/?>")
# 깨진 zip 이 낼 수 있는 오류들. 압축된 본문만 망가지면 BadZipFile 이 아니라 zlib.error 가 난다(2026-11-13 리뷰)
UNREADABLE_ZIP = (OSError, zipfile.BadZipFile, KeyError, RuntimeError, EOFError, NotImplementedError, zlib.error)
SLIDE_PART = re.compile(r"^ppt/(slides/slide|notesSlides/notesSlide)(\d+)\.xml$")
HANGUL = re.compile(r"[가-힣]")


def load_terms(path=GLOSSARY):
    """용어집을 읽어 [{wrong, right, field, source, pattern}] 로. 첫 줄(열 이름)과 # 줄은 뺀다."""
    terms = []
    try:
        with open(path, encoding="utf-8") as handle:
            rows = [line.rstrip("\n").split("\t") for line in handle
                    if line.strip() and not line.startswith("#")]
    except OSError:
        return terms
    for row in rows[1:]:
        if len(row) < 2 or not row[0].strip():
            continue
        wrong, right = row[0].strip(), row[1].strip()
        words = [re.escape(word) for word in re.split(r"[\s\-]+", wrong) if word]
        body = r"[\s\-]+".join(words)
        # 영어는 낱말 단위로만 맞춘다(다른 낱말의 일부는 아니다). 한국어는 조사가 붙으므로 그대로.
        if not HANGUL.search(wrong):
            body = r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])"
        terms.append({"wrong": wrong, "right": right,
                      "field": row[2].strip() if len(row) > 2 else "",
                      "source": row[3].strip() if len(row) > 3 else "",
                      "pattern": re.compile(body, re.IGNORECASE)})
    return terms


def xml_paragraphs(xml_text):
    """XML 한 조각의 글을 문단 단위 줄로. 한 문단 안의 글 조각(run)들은 이어 붙인다."""
    with_breaks = PARAGRAPH_END.sub("\n", INLINE_BREAK.sub(" ", xml_text))
    return [html.unescape(XML_TAG.sub("", line)).strip() for line in with_breaks.split("\n")]


def office_units(path):
    """.pptx / .docx 의 글을 [(위치, 문단)] 으로. 읽을 수 없으면 []."""
    units = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if path.lower().endswith(".pptx"):
                parts = sorted((int(match.group(2)), match.group(1), name)
                               for name in names for match in [SLIDE_PART.match(name)] if match)
                for number, kind, name in parts:
                    label = ("slide %d" if kind.startswith("slides") else "slide %d notes") % number
                    text = archive.read(name).decode("utf-8", "replace")
                    units.extend((label, paragraph) for paragraph in xml_paragraphs(text) if paragraph)
            elif "word/document.xml" in names:
                text = archive.read("word/document.xml").decode("utf-8", "replace")
                units.extend(("paragraph %d" % index, paragraph)
                             for index, paragraph in enumerate(xml_paragraphs(text), 1) if paragraph)
    except UNREADABLE_ZIP:
        return []
    return units


def file_units(path):
    """파일의 글을 [(위치, 줄)] 으로. 이진 파일·없는 파일·용어집 자체는 []."""
    if not os.path.isfile(path) or os.path.realpath(path) == os.path.realpath(GLOSSARY):
        return []
    if path.lower().endswith((".pptx", ".docx")):
        return office_units(path)
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES)
    except OSError:
        return []
    if b"\0" in raw:
        return []
    return [("%d" % number, line) for number, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1)]


def find_wrong_terms(units, terms):
    """[(위치, 줄)] 에서 틀린 말을 찾는다 → [(위치, 용어 쌍)]. 백틱 안과 표시한 줄은 뺀다."""
    hits = []
    for location, line in units:
        if IGNORE_MARK in line:
            continue
        used = BACKTICK_SPAN.sub(" ", line)
        hits.extend((location, term) for term in terms if term["pattern"].search(used))
    return hits


def main():
    """주어진 파일(과 답변)에서 틀린 분야 용어를 찾아 한 줄씩 알린다."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", help="text, .md, .pptx or .docx files")
    parser.add_argument("--answer", help="a file holding the answer text; reported as '답변'")
    parser.add_argument("--exit-zero", action="store_true", help="exit 0 even when something is found")
    parser.add_argument("--limit", type=int, default=20, help="report at most this many hits")
    args = parser.parse_args()

    terms = load_terms()
    # 답변은 파일이 아니라서 임시 파일로 받는다. 그 임시 경로 대신 "답변" 으로 보여 줘야 읽는 쪽이 안다.
    sources =([("답변", args.answer)] if args.answer else []) + [(path, path) for path in args.paths]
    hits = []
    for label, path in sources:
        hits.extend((label, location, term) for location, term in find_wrong_terms(file_units(path), terms))
    for label, location, term in hits[:args.limit]:
        print("%s:%s [term] '%s' → '%s' — %s (%s)" % (label, location, term["wrong"], term["right"],
                                                    term["field"], term["source"]))
    if len(hits) > args.limit:
        print("… 그리고 %d건 더" % (len(hits) - args.limit))
    print("check_terms: %d건 — 파일 %d개" % (len(hits), len(sources)))
    return 1 if hits and not args.exit_zero else 0


if __name__ == "__main__":
    sys.exit(main())
