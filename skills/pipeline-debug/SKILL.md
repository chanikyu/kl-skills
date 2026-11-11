---
name: pipeline-debug
description: When code fails or gives a wrong result, trace the error back along the pipeline it ran in instead of patching the line where it surfaced. Map the stages first, then check what went into and came out of each stage - counts, columns, a few real values - against what was expected, until the first stage whose output is wrong. That stage is the cause; the place the error appeared is usually downstream of it. Reproduce the fault at that stage, pin it with a failing check, fix it there, then re-run from that stage to the end and confirm every downstream output again. Use this whenever an error, exception, traceback, failed test, crash or suspicious output appears in code you wrote or are running - especially multi-step data or analysis pipelines where stages hand files or tables to each other. Triggers - error, exception, traceback, failed, crash, bug, wrong result, unexpected output, NaN, empty output, pipeline, debug, troubleshoot, root cause, 에러, 오류, 실패, 버그, 디버깅, 트러블슈팅, 결과가 이상하다, 값이 비었다, 안 돌아간다, 파이프라인.
---

# Pipeline Debug

에러는 **원인보다 아래쪽에서** 보인다. 2단계에서 표를 잘못 합쳤는데, 에러는 5단계에서
`KeyError` 로 나온다. 5단계의 그 줄을 고치면 에러는 사라지지만 2단계의 틀린 표는 그대로
흘러간다. 이번엔 에러 없이 **틀린 결과**로.

그래서 에러가 난 줄로 바로 가지 않는다. 파이프라인을 따라 **처음 틀어진 단계**를 찾는다.

## 순서

### 1. 파이프라인을 먼저 그린다

단계마다 네 가지를 적는다. 그림이 없으면 따라갈 길이 없다.

| 단계 | 들어가는 것 | 나오는 것 | 돌리는 명령·함수 |
|---|---|---|---|
| 1. 읽기 | `raw/samples.tsv` | 표 (샘플 × 속성) | `load_samples()` |
| 2. 합치기 | 1단계 표 + `meta.tsv` | 합친 표 | `merge_metadata()` |
| 3. 거르기 | 2단계 표 | 기준을 넘은 행만 | `filter_by_depth()` |
| … | | | |

### 2. 에러가 보인 단계를 표시한다

거기는 **출발점**이지 원인이 있는 곳이 아니다. 에러 메시지와 그 단계 번호만 적어 둔다.

### 3. 입력부터 단계마다 확인한다

각 단계에서 **들어간 것과 나온 것을 숫자로** 본다. 눈으로 "괜찮아 보인다"는 확인이 아니다.

- 개수: 행 수, 파일 수, 레코드 수
- 모양: 열 이름, 값의 종류, 빈 칸 수
- 실제 값 몇 개: 맨 앞 세 줄
- **기대값**: 이 단계를 지나면 무엇이 되어야 하는가

`scripts/probe.py <파일...>` 가 파일 한 장의 개수·열·빈 칸·앞부분을 한 번에 뽑는다. 표(TSV·CSV),
JSON, 서열 파일 FASTA(= `>이름` 줄 다음에 염기·아미노산 서열이 오는 형식)를 읽는다. 단계 사이에 파일이 오가는 파이프라인이면 단계마다 한 번씩 부른다.

결과는 이 표 하나로 남긴다. **처음으로 "기대 ≠ 실제"가 된 단계가 원인 단계다.**

| 단계 | 들어간 것 | 나온 것 | 기대 | 실제 | 판정 |
|---|---|---|---|---|---|
| 1. 읽기 | 파일 1개 | 120행 × 8열 | 120행 | 120행 | 맞음 |
| 2. 합치기 | 120행 + 메타 118행 | 120행 | 120행, 빈 칸 0 | 120행, `site` 빈 칸 **2** | **처음 틀림** |
| 3. 거르기 | 120행 | 96행 | — | — | (2단계를 고친 뒤에 다시 본다) |

단계가 많으면 **가운데부터** 본다. 가운데가 맞으면 원인은 뒤쪽 절반, 틀리면 앞쪽 절반이다.
열 단계면 네 번 안에 찾는다.

### 4. 원인 단계에서 재현한다

그 단계만, 그 입력으로 다시 돌려서 같은 틀림이 나오는지 본다. **재현이 안 되면 원인이 아니다.**
다른 단계를 다시 본다.

### 5. 고치기 전에 실패하는 확인을 만든다

그 단계의 출력에 대한 확인 한 줄을 먼저 쓰고, 지금 **실패하는 것을 본다.**

```python
assert merged["site"].notna().all(), "메타데이터가 없는 샘플이 섞였다"
```

이 확인이 있으면 같은 자리가 다시 깨질 때 에러가 그 단계에서 바로 난다. 5단계까지
흘러가서 엉뚱한 곳에 나타나지 않는다.

### 6. 고치고, 그 단계부터 끝까지 다시 돌린다

원인 단계만 확인하고 끝내지 않는다. 고친 단계의 출력이 바뀌었으니 **아래 단계 전부가 바뀐다.**
3번의 표를 그 단계부터 다시 채운다. 고친 자리에서 새로 깨진 것이 아래에서 나타나는 경우가
여기서 잡힌다.

### 7. 보고한다

3번의 표 + 원인 단계 + **왜** 틀렸나 + 무엇을 고쳤나 + 아래 단계를 다시 확인한 결과.
에러가 사라진 것은 결과가 아니다. 아래 단계까지 기대대로 나오는 것이 결과다.

## 하지 말 것

- 에러 메시지가 가리키는 줄을 바로 고치기 — 그 줄은 증상이다
- `try/except` 로 에러를 삼켜서 "돌아가게" 만들기 — 틀린 결과가 조용히 흐른다
- 단계 출력을 숫자 없이 "봤다"고 넘어가기
- 원인 단계에서 재현하지 않고 고치기
- 고친 단계만 확인하고 아래 단계를 다시 안 보기
- 같은 문제를 두 번 고쳐도 안 되는데 세 번째를 같은 가설로 시도하기 — 멈추고 1번부터 다시
- 원인을 모르는데 그럴듯한 원인을 지어내기 — "아직 모른다, 3단계까지는 맞다"가 답이다

## 다른 규칙과의 경계

| 무엇을 정하나 | 어디 |
|---|---|
| 일반 디버깅 절차 (원인 → 패턴 → 가설 → 고치기) | `superpowers:systematic-debugging` |
| **파이프라인에서 원인 단계를 찾는 법** | 이 스킬 |
| 재현 못 하는 지적은 결함이 아니다 · 고치기 전에 실패 테스트 | `rules/common/code-verification.md` |
| 중간 파일을 저장하고 덮어쓰지 않기 | `analysis-artifacts` 스킬 |
| 결과를 보고하는 글 | `natural-answering` 스킬 |
