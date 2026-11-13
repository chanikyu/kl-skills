[English](readable-code.md) · **한국어** · [日本語](readable-code-ja.md) · [中文](readable-code-zh.md) · [Español](readable-code-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# readable-code

다음에 읽을 사람이 따라갈 수 있는 코드를 쓴다. 이름은 담긴 것을 말하고, 주석은 이유를 말한다.

## Claude 에서 쓰기

따로 말할 것은 없다. 코드를 쓰거나 바꿀 때마다 적용된다.

## 하는 일

1. 이름은 그 값이 무엇인지 말한다. `n` 이 아니라 `student_name` 이다.
2. 주석은 코드가 왜 그렇게 생겼는지 설명한다. 줄마다 무엇을 하는지 설명하지 않는다.
3. 값은 코드가 아니라 데이터 파일에 둔다([no-hardcoding](no-hardcoding-ko.md) 참고).

## 파일과 스크립트

| 스크립트 | 하는 일 |
| --- | --- |
| `check_code.py <files>` | 모호한 이름, 빠진 docstring(= 함수 맨 위에 쓰는 설명 글), 주석 없는 긴 함수를 알린다 |

허용하는 짧은 이름과 모호한 이름 목록은 `data/` 의 데이터 파일에 있다.

## 받쳐 주는 훅

`code-check` 는 Python 파일이 쓰일 때마다 돈다. 알리기만 하고 막지는 않는다.

## 한계

이 검사는 Python 만 읽는다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
