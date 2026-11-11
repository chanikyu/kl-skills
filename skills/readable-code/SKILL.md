---
name: readable-code
description: Write code the next reader can follow - name things after what they hold, and say why the code is the way it is. Use this whenever you write or change code in any language: a script, a notebook cell, a function, a one-off calculation. Names must say what is inside (student_name, timeout_seconds, matched_pages), never a, b, s, tmp, data or result. Every function says what it does and why it was built that way, every judgement call carries the reason it was made, and every value that came from somewhere says where. Comments that restate the code are the ones that go stale and start lying, so they are banned. Values, lists, mappings, paths and thresholds belong in files rather than in code - that part is the no-hardcoding skill, which this one points at instead of repeating. Triggers - code, script, function, variable, name, naming, rename, comment, docstring, readable, cleanup, refactor, 코드, 스크립트, 함수, 변수명, 이름, 주석, 설명문, 리팩터링, 정리, 읽기 쉽게.
---

# Readable Code

이 코드를 다시 읽는 사람은 **6개월 뒤의 나**다. 그때 남아 있는 것은 이름과 주석뿐이다.
그 자리에 `a`, `tmp`, 설명 없는 50줄 함수가 있으면, 코드를 다시 읽어서 머릿속에
복원해야 한다. 그 복원 비용이 이 스킬이 막으려는 것이다.

규칙은 세 가지이고, 첫 번째는 다른 스킬이 가지고 있다.

| 무엇 | 어디 |
|---|---|
| 값·목록·매핑·경로·임계값을 코드에 박지 않는다 | **`no-hardcoding` 스킬** (여기서 다시 쓰지 않는다) |
| 이름은 담긴 것을 말한다 | 이 스킬 |
| 왜 그렇게 했는지를 남긴다 | 이 스킬 |

## 이름 — 담긴 것을 그대로 쓴다

```python
# 나쁨
a = load(p)
for i in a:
    s = i["n"]
    tmp = calc(s)

# 좋음
samples = load(sample_table_path)
for sample in samples:
    strain_name = sample["name"]
    coverage_depth = estimate_coverage(strain_name)
```

지키는 것 네 가지다.

1. **두 글자 이하는 쓰지 않는다.** 예외는 반복 번호 `i`, `j`, `k` 와 버리는 값 `_` 뿐이다.
   `p` → `path`, `s` → `text`, `m` → `match`, `df` → `samples`
2. **길어도 모호한 이름을 피한다.** `data`, `tmp`, `result`, `info`, `value` 는 "무엇의"가
   빠져 있다. `data` → `allele_counts`, `tmp` → `merged_rows`, `result` → `matched_pages`
3. **단위와 종류를 이름에 넣는다.** `timeout` → `timeout_seconds`, `size` → `size_bytes`,
   `count` → `page_count`. 단위를 모르면 호출하는 쪽이 매번 추측한다
4. **참거짓 값은 `is_`·`has_`·`should_` 로 시작한다.** `valid` → `is_valid`,
   `cache` → `has_cache`

이름을 늘리기 어렵다면 그 변수가 **두 가지를 담고 있다**는 신호다. 그때는 이름이 아니라
코드를 나눈다.

## 주석 — "자세하게"가 무슨 뜻인가

자세한 주석은 **코드를 되풀이하는 주석이 아니다.** 그쪽은 가장 먼저 낡아서 거짓말을 한다.

```python
# 나쁨 — 코드를 한국어로 옮긴 것. 1이 2로 바뀌면 주석이 거짓이 된다
retry_count += 1   # retry_count 를 1 늘린다

# 좋음 — 코드가 말하지 못하는 것
# 서버가 죽었을 때 몰려가지 않도록 기다리는 시간을 2배씩 늘린다. 30초에서 멈추는 것은
# 그 위로는 사용자가 멈춘 줄로 오해하기 때문이다.
delay_seconds = min(2 ** retry_count, 30)
```

남길 것 네 가지다.

1. **함수마다 설명문** — 무엇을 하는가, 그리고 **왜 이렇게 만들었는가**. 두 번째가 빠지면
   다음 사람이 "이건 왜 이렇게 복잡한가"에 답할 수 없어서 그냥 다시 쓴다
2. **판단이 들어간 자리** — 고른 것, 버린 것, 버린 이유. 선택지가 둘 이상이었던 자리마다
3. **값의 출처** — 그 숫자가 논문·문서·측정 중 어디서 왔는지. 측정이면 결과 파일 경로까지
4. **일부러 자른 모서리** — 천장과 올리는 방법을 같이 적는다
   (`# 전체 락이라 처리량이 문제되면 계정별 락으로 나눈다`)

안 적어도 되는 것: 코드를 읽으면 그대로 보이는 것. `# 파일을 연다` 는 `open()` 위에 쓸 말이 아니다.

## 기계로 먼저 걸러내기

```bash
scripts/check_code.py <파일.py...>        # 경고만
scripts/check_code.py --all <파일.py...>  # 참고 등급까지
```

잡는 것:

- `vague-name` — 두 글자 이하이거나, 길지만 모호한 이름
- `no-docstring` — 다섯 줄 넘는 함수·클래스에 설명문이 없다
- `uncommented-long-function` — 스무 줄 넘는 함수 안에 주석이 한 줄도 없다
- `no-module-docstring` — 파일이 무엇을 하는 파일인지 맨 위에 안 적혀 있다

파이썬에 들어 있는 분석기(`ast`)로 구문을 읽으므로 문자열 속 글자를 변수로 착각하지 않는다.
**파이썬만 본다.** 다른 언어는 위 규칙을 손으로 적용한다.

판정 기준은 `data/` 에 있다 — 허용할 짧은 이름은 `short-names-ok.txt`, 모호하다고 볼 이름은
`vague-names.txt`. 도메인에서 통하는 짧은 이름이 있으면 그 파일에 한 줄 더한다.
코드를 고치지 않는다.

**스크립트가 조용한 것이 잘 썼다는 뜻은 아니다.** 주석이 *맞는 말인지*, 이름이 *정확한지*는
기계가 못 본다. `# 왜` 자리에 거짓이 들어 있어도 통과한다. 검사는 빠진 자리를 가리킬 뿐이다.

## 다른 규칙과의 경계

| 무엇을 정하나 | 어디 |
|---|---|
| 값을 코드에 박지 않기 | `no-hardcoding` 스킬 |
| TypeScript·React 쪽 관례 (파일 이름, 폴더 구조) | `coding-standards` 스킬 |
| 사용자에게 쓰는 글 | `natural-answering` 스킬 |
| 불변성·파일 크기·중첩 깊이 | `~/.claude/rules/common/coding-style.md` |
| 이름과 주석 | 이 스킬 |

## 하지 말 것

- `a`, `b`, `s`, `p`, `tmp`, `data`, `result` 같은 이름
- 단위 없는 숫자 이름 (`timeout`, `size`)
- 설명문 없는 여러 줄 함수
- 코드를 되풀이하는 주석
- 판단한 자리에 이유를 안 남기기
- 일부러 자른 모서리를 말없이 두기
- 검사가 조용하다고 다 됐다고 보기
