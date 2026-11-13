[English](no-hardcoding.md) · **한국어** · [日本語](no-hardcoding-ja.md) · [中文](no-hardcoding-zh.md) · [Español](no-hardcoding-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# no-hardcoding

값, 목록, 매핑(= 이것을 저것으로 바꾸는 짝 표), 경로, 임계값(= 판단을 가르는 기준 숫자)을 코드 밖에 둔다.

## Claude 에서 쓰기

따로 말할 것은 없다. 코드에 값이 들어가려 할 때마다 적용된다.

## 하는 일

1. 이미 파일에 있는 값은 그 파일에서 읽는다. 코드에 베껴 넣지 않는다.
2. 매핑 표, 별칭 목록(= 같은 것을 가리키는 다른 이름들), 대상 목록은 데이터 파일(`.tsv`, `.json`)에 넣는다.
3. 경로는 스크립트 위치에서 계산하거나, 인자로 받거나, 환경 변수(= 프로그램 밖에서 넘겨주는 설정값)에서 읽는다.
4. 임계값, 시드(= 무작위 결과를 똑같이 다시 내게 하는 시작 숫자), 개수는 명령줄 인자로 받는다.
5. 절대 바뀌지 않는 상수만 코드에 남긴다. 그때도 이름과 출처를 붙인다.

## 한계

모델이 따를 규칙이다. 이것을 직접 검사하는 스크립트는 없다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
