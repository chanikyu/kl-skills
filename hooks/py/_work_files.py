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


def wiki_root():
    """위키 뿌리. 환경 변수가 먼저고, 없으면 ~/llm-wiki-docs."""
    return os.environ.get("LLM_WIKI_ROOT") or os.path.join(os.path.expanduser("~"), "llm-wiki-docs")


def is_skipped(path):
    """캐시·임시 폴더처럼 사용자가 직접 쓴 것이 아닌 자리인가."""
    normalised = path.replace("\\", "/")
    return any(part in normalised for part in SKIP_PARTS)


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
