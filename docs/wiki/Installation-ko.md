[English](Installation.md) · **한국어** · [日本語](Installation-ja.md) · [中文](Installation-zh.md) · [Español](Installation-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# 설치

## 필요한 것

| 필요한 것 | 쓰는 곳 | 없으면 |
| --- | --- | --- |
| Claude Code | 플러그인(= Claude Code 에 덧붙이는 기능 묶음)을 설치하고 훅(= 정해진 순간에 저절로 도는 명령)을 돌린다 | 아무것도 설치되지 않는다 |
| `python3` | 게이트 대부분과 모든 스킬 스크립트(표준 라이브러리만 쓴다) | 그 게이트들은 조용히 건너뛴다 |
| `git` | 계획 이탈(= 계획에서 벗어난 일) 검사 | 그 검사를 건너뛴다 |

미리 빌드한(= 바로 돌릴 수 있게 미리 만들어 둔) 게이트가 함께 들어 있다. macOS 용은 Apple silicon 과 Intel 칩을 지원한다.
Linux 용은 x86_64(= 대부분의 PC 에 쓰는 칩 종류)와 ARM(= 휴대폰과 일부 노트북에 쓰는 칩 종류)을 지원한다.
Linux 용은 WSL(= Windows 안에서 Linux 를 돌리는 기능)에서도 돈다. Windows 용은 x86_64 를 지원한다.
그 밖의 환경에서는 게이트가 아무 말 없이 통과시킨다.

## 설치하기

Claude Code 에서 입력한다.

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

첫 줄은 이 저장소를 마켓플레이스(= 플러그인을 찾아 내려받는 목록)로 추가한다. 둘째 줄은 플러그인을 설치한다.

## 잘 됐는지 확인하기

훅은 세션(= Claude Code 를 켜서 끌 때까지의 한 번의 대화)이 시작할 때 읽힌다. 그래서 Claude Code 를 다시 시작한다.
새 세션의 첫 줄은 이렇게 나와야 한다.

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

배너(= 첫 줄에 뜨는 안내 문구)가 없으면 훅이 돌지 않는 것이다. `/plugin` 을 열어 `kl-skills` 가 켜져 있는지 확인한다.

## 업데이트

```sh
claude plugin marketplace update kl-skills
claude plugin update kl-skills@kl-skills
```

그다음 세션을 다시 시작한다.

## 지우기

```sh
claude plugin uninstall kl-skills@kl-skills
```

지워도 남는 것이 있다. `~/llm-wiki-docs/` 에 있는 위키와 그 그래프, 계획서, `~/.claude/checklists/` 에 있는 체크리스트다.
이것들은 플러그인의 것이 아니라 사용자의 것이다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
