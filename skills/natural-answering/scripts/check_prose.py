#!/usr/bin/env python3
"""natural-answering — 글에서 기계로 잡히는 것만 잡는다.

    check_prose.py [--all] [--limit N] [--max-sentence N] FILE [FILE...]

자연스러움은 기계가 못 재지만, **빠진 것**은 상당 부분 잡힌다. 그래서 이 스크립트는
"잘 썼나"를 판정하지 않고, 읽는 사람이 되묻게 될 자리만 가리킨다:

  - 뜻을 안 붙이고 던진 약어와 영문 용어   (§0-2 규칙 2)
  - 비교 기준 없는 숫자                     (§0-2 규칙 3)
  - 한 번에 읽히지 않는 긴 문장
  - 연결어미로 끝나 주절이 빠진 문장
  - 주어가 빠졌을 가능성이 큰 문장
  - "더 빠르다"처럼 비교 대상이 빠진 말
  - "전부 통과"처럼 개수가 빠진 말          (§15)
  - 길잡이 문장 없이 바로 나오는 표
  - 이중 수동·번역투 (패턴은 data/patterns.tsv)

판정 기준은 전부 data/ 의 파일에서 읽는다. 문턱값은 인자로 바꾼다.
코드블록·인라인 코드·표 안쪽·URL·경로는 글이 아니므로 검사에서 뺀다.

등급은 둘이다. warn 은 기본 출력, note 는 --all 일 때만 — note 쪽은 일부러
위양성을 감수한 검사(주어 생략 추정 등)라, 매번 보이면 잡음이 된다.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿️]"
)
HANGUL = re.compile(r"[가-힣]")
# 코드·경로·URL·식별자: 글이 아니라 이름이므로 용어 검사에서 뺀다.
CODE_SPAN = re.compile(r"`[^`]*`")
# 인용부호 안은 이름이거나 남의 말이다. 한국어 글에서 영어 제목을 인용하면 그 안의 낱말이
# 전부 "뜻 없는 용어"로 걸리는데, 그건 용어를 던진 게 아니라 제목을 가리킨 것이다.
QUOTED = re.compile(r"[\"“][^\"”\n]{2,}[\"”]")
# [[링크]] 안은 가리키는 페이지의 이름이다. 뜻을 붙일 용어가 아니라 주소다.
WIKILINK = re.compile(r"\[\[[^\]\n]*\]\]")
# 인용은 글이 아니라 출처 표시다. 안에 든 저자 이름(van Nood)·학술지 이름(PNAS)은 뜻을 붙일
# 용어가 아니다 — 2026-11-11 에 이것들이 "뜻 없는 용어" 로 잡혀 답변이 여러 번 막혔다.
# HTML 태그와 GitHub 알림 표시([!NOTE] 등)는 글이 아니라 문서의 뼈대다. README 의 배지 묶음이
# "195자짜리 문장" 으로, <summary><strong> 이 "뜻 없는 용어" 로 잡혔다(2026-11-11). 태그만 지우고
# 태그 사이의 글은 그대로 검사한다.
HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*"
                      r"(?:\s+[A-Za-z_:][A-Za-z0-9_:.-]*(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s<>]+))?)*\s*/?>")
GITHUB_ALERT = re.compile(r"\[![A-Z]+\]")
MARKDOWN_LINK = re.compile(r"\[[^\]\n]*\]\([^)\n]*\)")
CITATION = re.compile(r"\[[^\]\n]*\b(?:1[89]|20)\d{2}[a-z]?\b[^\]\n]*\]")
# 참고문헌 목록의 한 줄: "[저자 연도] 설명. 학술지. <주소>" 또는 "[1] ...". 주소가 있어야 한다.
MAX_GLOSSARY_TERM_WORDS = 3   # "dysbiosis(장내 미생물 불균형)" 처럼 괄호를 빼면 이름은 길어야 세 낱말
SOURCE_ENTRY = re.compile(r"^\[(?:\d+|[^\]\n]*\b(?:1[89]|20)\d{2}[a-z]?\b[^\]\n]*)\]")
URL = re.compile(r"(?:https?://|file://|www\.)\S+")
PATHLIKE = re.compile(r"[~./]?[\w.-]*[/\\][\w./\\-]+|\b[\w-]+\.(?:py|sh|md|json|tsv|txt|toml|html|rs|ps1|yml|yaml|csv)\b")
IDENT = re.compile(r"\b\w*(?:_|[a-z][A-Z])\w*\b")  # snake_case, camelCase, PascalCase
ACRONYM = re.compile(r"\b[A-Z]{2,6}\b")
LATIN_WORD = re.compile(r"\b[a-z][a-z-]*[a-z]\b")
NUMBER_WITH_UNIT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|배|개|건|초|분|시간|ms|s|bp|KB|MB|GB|점|명|쌍)")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|(?<=[。!?])")


def load_lines(name, data_dir=None):
    path = os.path.join(data_dir or DATA, name)
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    except OSError:
        pass
    return out


def load_patterns(data_dir=None):
    pats = []
    for line in load_lines("patterns.tsv", data_dir):
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        rx, sev, msg = parts[0], parts[1].strip(), parts[2]
        fix = parts[3] if len(parts) > 3 else ""
        try:
            pats.append((re.compile(rx), sev, msg, fix))
        except re.error as e:
            print("patterns.tsv: 정규식을 읽을 수 없다: %s (%s)" % (rx, e), file=sys.stderr)
    return pats


def is_glossed(body, tok):
    """그 자리에서 뜻을 붙였는가.

    세 가지 형태를 모두 인정한다. 쓰는 사람은 이 중 아무 것이나 고르기 때문이다:
      용어(= 뜻)        — 용어 뒤에 괄호
      뜻(= 용어)        — 괄호 안에 용어. 한국어 글에서 더 자연스러운 쪽이다
      뜻(용어)          — 등호 없이 괄호만
      용어 ... = 뜻      — 용어집 줄. "pks+ 대장균 = ..." 처럼 등호 앞에 용어가 있다
    """
    t = re.escape(tok)
    # 용어집 줄은 등호 앞이 이름 하나다("pks+ 대장균", "HUNT(...)"). 괄호 밖 낱말이 이보다 많으면
    # "AUC 가 0.9 라서 기준 = 0.5" 같은 보통 문장이다 — 그런 줄까지 정의로 보면 약어를 놓친다.
    term_side = body.split(" = ", 1)[0] if " = " in body else ""
    words_outside_brackets = re.sub(r"[(（][^)）]*[)）]", " ", term_side).split()
    if (len(words_outside_brackets) <= MAX_GLOSSARY_TERM_WORDS
            and re.search(r"(?<![A-Za-z])" + t + r"(?![A-Za-z])", term_side)):
        return True
    return bool(
        re.search(t + r"\s*[(（=:—–-]", body)
        or re.search(r"[(（]\s*=?\s*[^)）]*" + t, body)
    )


def mask(line):
    """글이 아닌 부분을 지운다. 길이는 유지하지 않는다 — 줄 번호만 쓰기 때문."""
    for rx in (CODE_SPAN, HTML_TAG, GITHUB_ALERT, QUOTED, WIKILINK, MARKDOWN_LINK, CITATION, URL,
               PATHLIKE, IDENT):
        line = rx.sub(" ", line)
    return line


def split_units(lines):
    """문단을 '한 번에 읽는 단위'로 나눈다. 목록은 항목마다 하나다.

    이걸 안 하면 불릿 두 개가 한 문장으로 붙어서, 있지도 않은 긴 문장이 만들어진다.
    """
    units, cur = [], []
    for line in lines:
        if re.match(r"^([-*>]|\d+[.)])\s", line) and cur:
            units.append(" ".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        units.append(" ".join(cur))
    return units


def split_sentences(text):
    parts = []
    for chunk in SENTENCE_SPLIT.split(text):
        chunk = (chunk or "").strip()
        # 0.5.0 처럼 숫자 사이 마침표에서 잘린 조각은 앞 문장에 다시 붙인다.
        if parts and (re.match(r"^\d", chunk) and re.search(r"\d$", parts[-1])):
            parts[-1] = parts[-1] + "." + chunk
        elif chunk:
            parts.append(chunk)
    return parts


class Doc:
    """마크다운에서 '사람이 읽는 문장'만 줄 번호와 함께 남긴다."""

    def __init__(self, text):
        self.prose = []        # (줄번호, 원문, 마스킹된 문장)
        self.paragraphs = []   # (시작 줄번호, [원문 줄...])
        self.tables = []       # (줄번호, 바로 앞 비어 있지 않은 줄)
        self.textlines = []    # (줄번호, 원문) — 코드블록 밖. 경로 검사용
        self.raw = text

        lines = text.splitlines()
        in_fence = False
        in_front = False
        para, para_start, prev_real = [], None, ""

        for i, line in enumerate(lines, 1):
            s = line.strip()
            if i == 1 and s == "---":
                in_front = True
                continue
            if in_front:
                if s == "---":
                    in_front = False
                continue
            if s.startswith("```") or s.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            # 표 행은 앞뒤 | 를 생략해도 되는 문법이다. `|` 로 시작하는 줄만 표로 보면,
            # 생략한 표의 칸들이 '아주 긴 문장' 으로 잡힌다.
            is_row = s.startswith("|") or s.count("|") >= 2
            prev_row = prev_real.startswith("|") or prev_real.count("|") >= 2
            if is_row:
                if not prev_row:
                    self.tables.append((i, prev_real))
                prev_real = s
                continue
            if not s:
                if para:
                    self.paragraphs.append((para_start, para))
                    para, para_start = [], None
                continue

            prev_real = s
            self.textlines.append((i, s))
            if para_start is None:
                para_start = i
            para.append(s)

            if s.startswith("#") or re.match(r"^[-*>\d]+[.)]?\s*$", s):
                continue
            body = re.sub(r"^[-*>]\s+|^\d+[.)]\s+", "", s)
            self.prose.append((i, body, mask(body)))

        if para:
            self.paragraphs.append((para_start, para))


def check(path, text, cfg, patterns, acronyms, terms, baseline):
    doc = Doc(text)
    found = []

    def add(line, sev, code, msg, fix=""):
        found.append({"path": path, "line": line, "sev": sev, "code": code, "msg": msg, "fix": fix})

    seen_acronym, seen_term = set(), set()

    for lineno, body, masked in doc.prose:
        korean = bool(HANGUL.search(body))

        for rx, sev, msg, fix in patterns:
            if rx.search(masked):
                add(lineno, sev, "pattern", msg, fix)

        # 참고문헌 줄의 학술지 약어(NEJM)는 이름이지 용어가 아니다. 본문 문장은 그대로 검사한다.
        if SOURCE_ENTRY.match(body) and URL.search(body):
            continue

        for tok in ACRONYM.findall(masked):
            if tok in acronyms or tok.lower() in terms or tok in seen_acronym:
                continue
            seen_acronym.add(tok)
            # 뒤에 괄호·등호·줄표가 붙어 있으면 그 자리에서 풀어 쓴 것으로 본다.
            if not is_glossed(body, tok):
                add(lineno, "warn", "undefined-acronym",
                    "약어 %s 를 뜻 없이 썼다. 처음 나올 때 한 줄로 풀어 쓴다" % tok,
                    "%s(= 쉬운 뜻 한 문장)" % tok)

        if korean:
            for tok in LATIN_WORD.findall(masked):
                low = tok.lower()
                if low in terms or low in seen_term:
                    continue
                # 앞 낱말이 대문자로 시작하면 학명·제품명 같은 고유명사다(S. aureus,
                # Staphylococcus aureus). 뜻을 붙일 용어가 아니라 이름이므로 넘어간다.
                if re.search(r"[A-Z][a-zA-Z]*\.?\s+" + re.escape(tok), body):
                    continue
                seen_term.add(low)
                if not is_glossed(body, tok):
                    add(lineno, "warn", "undefined-term",
                        "영문 용어 '%s' 를 뜻 없이 한국어 문장에 넣었다" % tok,
                        "%s(= 쉬운 뜻 한 문장, 가능하면 비유)" % tok)


    for start, lines in doc.paragraphs:
        blob = " ".join(lines)
        for unit in split_units(lines):
          for sent in split_sentences(mask(unit)):
            korean = bool(HANGUL.search(sent))
            # 같은 뜻을 담는 데 한국어는 글자를 덜 쓴다. 그래서 기준이 다르다.
            limit = cfg.max_sentence if korean else cfg.max_sentence_en
            if len(sent) > limit:
                add(start, "warn", "long-sentence",
                    "문장이 %d자다(기준 %d자). 한 문장에 한 가지 생각만 담는다"
                    % (len(sent), limit),
                    "접속사 자리에서 두 문장으로 끊는다")
            if re.search(r"더\s*(빠르|빠릅|빠른|느리|느립|느린|좋|낫|낮|많|적|크|큽|작|높)", sent) \
                    and not re.search(r"보다|비해|대비|기준|중에서", sent):
                add(start, "note", "missing-comparison",
                    "'더 ~'라고만 했다. 무엇과 견준 것인지가 빠졌다", "A보다 더 빠르다")
            if re.search(r"(전부|모두|다)\s*(통과|성공|실패|완료|처리|수정)", sent) \
                    and not re.search(r"\d", sent):
                add(start, "note", "missing-count",
                    "'전부/모두'에 개수가 없다. 총 몇 개 중 몇 개인지 쓴다",
                    "총 N개 중 M개 통과, K개 건너뜀(사유)")
            if korean and re.search(r"(이면|라면|으면|면)\s", sent) \
                    and not re.search(r"[\w가-힣](은|는|이|가)\s", sent):
                add(start, "note", "missing-subject",
                    "조건절만 있고 무엇이 그렇게 되는지(주어)가 안 보인다",
                    "위키 밖이면 끝난다 → 위키 밖이면 게이트가 바로 끝낸다")

        bolds = len(re.findall(r"\*\*[^*]+\*\*", blob))
        # 목록은 항목마다 볼드로 머리말을 다는 게 정상이다. 목록 줄이 하나라도 있으면 세지 않는다.
        listish = sum(1 for l in lines if re.match(r"^([-*>]|\d+[.)])\s", l))
        if bolds > cfg.max_bold and listish == 0:
            add(start, "warn", "bold-overuse",
                "한 문단에 볼드가 %d개다(기준 %d개). 다 강조하면 강조가 아니다" % (bolds, cfg.max_bold))
        if len(blob) > cfg.max_paragraph:
            add(start, "note", "long-paragraph",
                "문단이 %d자다(기준 %d자). 생각이 바뀌는 자리에서 끊는다" % (len(blob), cfg.max_paragraph))
        if NUMBER_WITH_UNIT.search(mask(blob)) and not any(w in blob for w in baseline):
            add(start, "note", "number-without-baseline",
                "숫자에 비교 기준이 없다. 좋은 건지 나쁜 건지 함께 쓴다",
                "34bp (read 길이 100bp보다 훨씬 짧다 = 안전하다)")
        marks = len(re.findall(r"`[^`\n]+`", blob))
        if marks > cfg.max_code_marks:
            add(start, "note", "code-mark-heavy",
                "한 문단에 백틱이 %d개다(기준 %d개). 이쯤이면 글이 아니라 목록이다"
                % (marks, cfg.max_code_marks),
                "이름을 나열하는 자리라면 목록으로 빼고, 문장은 문장으로 둔다")

        shorts = [s for s in split_sentences(mask(blob)) if 0 < len(s) < 12]
        if len(shorts) >= 3:
            add(start, "note", "period-spam",
                "짧은 조각마다 마침표를 찍어 리듬이 끊긴다. 이어 쓴다")

    for lineno, before in doc.tables:
        if not before or before.startswith("#"):
            add(lineno, "note", "table-without-lead-in",
                "표가 길잡이 문장 없이 바로 나온다. 표에서 무엇을 봐야 하는지 한 줄 먼저 쓴다",
                "두 번째 지표가 결론을 냈다. 왜 그런지가 아래 표다")

    # 같은 문장이 두 번 나오면, 둘 중 하나는 읽는 사람의 시간만 쓴다. 맨 앞 결론을
    # 아래 절에서 다시 설명하는 것이 가장 흔한 형태다.
    seen_sentence = {}
    for start, lines in doc.paragraphs:
        for unit in split_units(lines):
            for sent in split_sentences(mask(unit)):
                key = re.sub(r"\s+", " ", sent).strip()
                if len(key) < 20:
                    continue
                if key in seen_sentence:
                    add(start, "warn", "repeated-sentence",
                        "같은 문장을 두 번 썼다(%d행에도 있다). 한 번만 쓴다"
                        % seen_sentence[key],
                        "맨 앞 결론을 아래에서 다시 설명하지 않는다")
                else:
                    seen_sentence[key] = start

    # 문서에 적힌 경로가 실제로 있는지. 없는 경로는 문서가 코드와 어긋났다는 가장 선명한 신호다.
    # 예시용·자리표시 경로까지 같이 걸리므로 등급은 note 로 둔다(훅에서는 안 보인다).
    seen_path = set()
    for lineno, raw in doc.textlines:
        for tok in re.findall(r"[~\w.][\w./~-]*/[\w./~-]+", raw):
            if tok in seen_path:
                continue
            seen_path.add(tok)
            if any(c in tok for c in "<>*$?{}") or "..." in tok or "//" in tok:
                continue
            if not re.search(r"\.\w{1,6}$", tok) and not tok.endswith("/"):
                continue
            cand = os.path.expanduser(tok)
            here = os.path.dirname(os.path.abspath(path))
            bases = [here, os.path.dirname(here), cfg.root or "."]
            if os.path.isabs(cand) and os.path.exists(cand):
                continue
            if any(os.path.exists(os.path.join(b, cand)) for b in bases):
                continue
            if os.path.isabs(cand) or cand.startswith("~"):
                add(lineno, "note", "missing-path",
                    "문서가 가리키는 경로가 이 컴퓨터에 없다: %s" % tok,
                    "실제 경로로 고치거나, 예시임을 밝힌다")
            else:
                add(lineno, "note", "missing-path",
                    "문서가 가리키는 파일이 없다: %s" % tok,
                    "실제 구현과 대조해 고친다")

    emoji = len(EMOJI.findall(text))
    if emoji >= cfg.max_emoji:
        add(1, "warn", "emoji-spam", "이모지가 %d개다. 장식용 이모지는 쓰지 않는다" % emoji)

    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description="글에서 기계로 잡히는 생략·어색함을 찾는다.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--all", action="store_true", help="note 등급까지 보여준다")
    ap.add_argument("--limit", type=int, default=0, help="이 개수까지만 출력(0=전부)")
    ap.add_argument("--max-sentence", type=int, default=90, help="한국어 문장 기준 글자 수")
    ap.add_argument("--max-sentence-en", type=int, default=180, help="한글이 없는 문장 기준 글자 수")
    ap.add_argument("--max-bold", type=int, default=3)
    ap.add_argument("--max-paragraph", type=int, default=700)
    ap.add_argument("--max-emoji", type=int, default=3)
    ap.add_argument("--max-code-marks", type=int, default=6,
                    help="한 문단에 허용할 인라인 코드 개수")
    ap.add_argument("--exit-zero", action="store_true", help="찾아도 0으로 끝낸다(훅용)")
    ap.add_argument("--data-dir", default=None,
                    help="판정 기준 파일을 둔 디렉토리(기본: 이 스크립트 옆 data/)")
    ap.add_argument("--root", default=None,
                    help="상대 경로를 맞춰 볼 기준 디렉토리(기본: 문서가 든 git 저장소 뿌리)")
    cfg = ap.parse_args(argv)

    if cfg.root is None:
        d = os.path.dirname(os.path.abspath(cfg.files[0]))
        while d != "/" and not os.path.isdir(os.path.join(d, ".git")):
            d = os.path.dirname(d)
        cfg.root = d if os.path.isdir(os.path.join(d, ".git")) else "."

    patterns = load_patterns(cfg.data_dir)
    acronyms = set(load_lines("known-acronyms.txt", cfg.data_dir))
    terms = set(w.lower() for w in load_lines("known-terms.txt", cfg.data_dir)) \
        | set(a.lower() for a in acronyms)
    baseline = load_lines("baseline-words.txt", cfg.data_dir)

    found = []
    for path in cfg.files:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print("읽을 수 없다: %s (%s)" % (path, e), file=sys.stderr)
            continue
        found += check(path, text, cfg, patterns, acronyms, terms, baseline)

    warns = [f for f in found if f["sev"] == "warn"]
    notes = [f for f in found if f["sev"] != "warn"]
    show = warns + (notes if cfg.all else [])
    show.sort(key=lambda f: (f["path"], f["line"]))
    if cfg.limit and len(show) > cfg.limit:
        rest = len(show) - cfg.limit
        show = show[:cfg.limit]
    else:
        rest = 0

    for f in show:
        print("%s:%d [%s] %s" % (f["path"], f["line"], f["code"], f["msg"]))
        if f["fix"]:
            print("    고친 예: %s" % f["fix"])
    if rest:
        print("... 그리고 %d건 더 (--limit 를 올리거나 직접 돌려서 전부 본다)" % rest)

    tail = "경고 %d건" % len(warns)
    if cfg.all:
        tail += ", 참고 %d건" % len(notes)
    elif notes:
        tail += " (참고 %d건은 --all 로 본다)" % len(notes)
    print("natural-answering: %s — 파일 %d개" % (tail, len(cfg.files)))

    return 0 if (cfg.exit_zero or not warns) else 1


if __name__ == "__main__":
    sys.exit(main())
