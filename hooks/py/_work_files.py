"""Which written files count as the user's own work.

Shared by code-check (which files to inspect) and answer-check (did this turn change
the user's work, so its answer must be a work report). One list, so the two gates
cannot disagree about what a scratch path is.
"""

import os

from _checklist import checklist_dir

# 내 작업이 아닌 자리. 캐시·가상환경·남의 패키지·임시 폴더. 여기까지 지적하면 게이트가 꺼진다.
SKIP_PARTS = ("__pycache__", "/.venv/", "/venv/", "/site-packages/", "/node_modules/",
              "/.git/", "/scratchpad/", "/.tox/", "/build/", "/dist/")


# 남이 만든 코드를 들여온 자리: vendor 폴더와 압축된 .min. 파일. code-check(이름 검사)만 건너뛴다.
# SKIP_PARTS 에 넣지 않는 까닭: 작업 보고 검사(is_work_file)도 그 목록을 쓰는데, 이런 파일을 고쳐도
# 프로젝트가 바뀐 것이라 보고는 해야 한다(2026-11-18 영향 확인). 압축 파일 하나에 지적이 2천 건 넘게 났다.
VENDOR_DIR = "/vendor/"
MINIFIED_MARK = ".min."


def wiki_root():
    """위키 뿌리. 환경 변수가 먼저고, 없으면 ~/llm-wiki-docs."""
    return os.environ.get("LLM_WIKI_ROOT") or os.path.join(os.path.expanduser("~"), "llm-wiki-docs")


def is_skipped(path):
    """캐시·임시 폴더처럼 사용자가 직접 쓴 것이 아닌 자리인가."""
    normalised = path.replace("\\", "/")
    return any(part in normalised for part in SKIP_PARTS)


def is_not_own_code(path):
    """남이 만든 코드를 들여온 자리인가(vendor 폴더, 이름에 .min. 이 든 압축 파일). 이름 검사만 건너뛴다."""
    normalised = path.replace("\\", "/")
    return VENDOR_DIR in normalised or MINIFIED_MARK in os.path.basename(normalised)


def is_work_file(path):
    """작업 보고를 해야 하는 파일인가. 임시 자리, 위키 페이지, 체크리스트는 빼고 나머지는 다 작업이다.

    위키 페이지는 문서라서 llm-wiki-docs 규약대로 보고한다. 체크리스트는 checklist-check 가
    매 턴 쓰라고 하는 파일이라, 그걸 쓴 것만으로 작업 보고를 요구하면 질문에 답한 턴까지
    막힌다(2026-11-13 두 게이트가 부딪혔다). 작업 보고 6단계는 코드·설정·프로젝트 문서를 바꾼 턴에 쓴다.
    """
    if not path or is_skipped(path):
        return False
    real_path = os.path.realpath(path)
    return not any(real_path.startswith(os.path.realpath(root) + os.sep) for root in (wiki_root(), checklist_dir()))
