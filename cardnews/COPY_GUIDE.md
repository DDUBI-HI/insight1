# 카드뉴스 문구·구성 가이드

`/cardnews` 에이전트와 사람이 `deck.json` 을 쓸 때 따르는 기준입니다.
브랜드 문체 전체는 루트 `README.md` 의 **Voice and content**, **Card news** 를 따릅니다.

## 1. 문체

- "~합니다 / ~입니다" 존댓말 평서문. 고객은 "고객사", 독자는 "HR 담당자·교육 담당자"로 부릅니다. "여러분" 금지.
- **카드 한 장 = 주장 한 개.** 제목이 주장이고, 나머지는 그 근거나 방법입니다.
- 목록은 명사구나 짧은 평서문으로 씁니다. 목록 안에는 마침표를 찍지 않습니다. 묶을 때는 " · "(가운뎃점)을 씁니다.
- 대비 화법을 즐겨 씁니다: "A보다 B", "A가 아니라 B", "A를 넘어 B".
- **이모지는 쓰지 않습니다.**
- **근거 없는 수치·통계·인용은 쓰지 않습니다.** 수치나 프레임워크를 쓰면 `deck.json` 의 `sources` 에 출처를 적습니다.
  예: `{ "claim": "...", "source": "Kirkpatrick 4단계 평가 모델" }`
  확인할 수 없으면 수치 대신 질적 표현("빠르게 늘고 있습니다"가 아니라 "~로 옮겨가고 있습니다")을 씁니다.
- 영문은 라벨에만 씁니다: `kicker`, STEP 라벨, 프로그램 이름(예: AI × JOB). 문장은 한국어로 씁니다.

## 2. 덱 구성

표준은 **13장**이고, 최소 7장, 최대 20장입니다.

| 순서 | 역할 | 권장 템플릿 |
|---|---|---|
| 1 | 표지: 주제 + 후킹 | `cn-cover` (필수) |
| 2 | 도입: 왜 지금인가 | `cn-intro` |
| 3–4 | 전체 그림 | `cn-compare` (무엇이 바뀌었나), `cn-summary` (N가지 한눈에) |
| 5–9 | 본문: 항목별 1장 | `cn-feature` · `cn-story` · `cn-split` · `cn-grid` · `cn-steps` 를 번갈아 |
| 10 | 독자 참여 | `cn-checklist` (셀프 점검) |
| 11 | 자주 묻는 질문 | `cn-faq` |
| 12 | 결론 한 문장 | `cn-statement` |
| 13 | CTA | `cn-closing` (필수) |

- 같은 템플릿을 연달아 쓰지 않습니다. 생성기가 오류로 처리합니다.
- 구조 카드는 행이 적으면 아래가 비어 보입니다. `cn-compare` 는 3–4행, `cn-steps` 는 4단계, `cn-summary` 는 4–5행, `cn-split` 체크는 3개를 권장합니다.
- 사진 카드(cover/intro/feature/story/split/faq/closing)와 사진 없는 카드를 섞어 넘길 때 리듬을 만듭니다.
- 본문 항목이 N개면 `cn-summary` 의 행 수와 본문 카드 수를 N으로 맞추고, `kicker` 를 `TREND 01`처럼 번호로 이어 줍니다.

## 3. 내용 → 템플릿 고르기

| 내용의 모양 | 템플릿 |
|---|---|
| 이전 vs 지금, A vs B | `cn-compare` (2–4행) |
| N가지 목록 개요 | `cn-summary` (3–5행) |
| 사진으로 보여줄 개념 하나 + 한 줄 설명 | `cn-feature` |
| 사진 + 3–4줄 설명 문단 | `cn-story` |
| 사진 + 실천 포인트 2–4개 | `cn-split` |
| 4가지 분류·단계·요소 | `cn-grid` (정확히 4칸, 강조 칸 `point: true`) |
| 순서가 있는 절차 | `cn-steps` (3–4단계, 핵심 단계 `point: true`) |
| 질문 3개 | `cn-checklist` |
| 질문 1개 + 답 1개 | `cn-faq` |
| 결론 메시지 | `cn-statement` |

## 4. `deck.json` 필드

공통: 각 카드에 `template`, `name`(영문 소문자·숫자·하이픈), 선택 `label`(HTML 주석)이 있습니다.
여러 줄 필드는 **문자열 배열**이며, 원소 하나가 한 줄입니다. 줄은 의미 단위로 직접 나눕니다.
표기: `*강조*` 는 포인트 블루(statement 제목에서는 하늘색 형광펜), `**굵게**` 는 굵은 포인트색(grid `note`)입니다.

사진 칸: `"photo": { "unsplash": "<ID>", "query": "<영문 검색어>", "alt": "<한국어 설명>", "file"?: "x.jpg", "position"?: "30% 50%" }`

| 템플릿 | 필드 (괄호는 최대 줄 수) |
|---|---|
| `cn-cover` | `pill`, `title`(2), `subtitle`, `photo` |
| `cn-intro` | `eyebrow`, `title`(2), `point`, `photo` |
| `cn-feature` | `kicker`?, `title`(2, 둘째 줄 `*강조*` 권장), `desc`(2), `photo` |
| `cn-story` | `eyebrow`, `title`(1), `body`(문단, 4줄 분량), `photo` |
| `cn-checklist` | `title`(1), `items[3]`: `num`?(예 "Q1"), `title`(1), `desc`(2) |
| `cn-faq` | `title`(2), `question`(2), `answer`(2), `photo` |
| `cn-closing` | `lead`(2), `title`(1), `photo` |
| `cn-compare` | `kicker`, `title`(2), `before_label`?("이전"), `after_label`?("지금"), `rows[2–4]`: `before`(2), `after`(2) |
| `cn-summary` | `kicker`, `title`(2), `rows[3–5]`: `title`, `desc` (번호 자동) |
| `cn-split` | `kicker`, `title`(2), `checks[2–4]`(각 1줄), `photo` |
| `cn-grid` | `kicker`, `title`(2), `sub`?, `tiles[4]`: `title`, `desc`, `point`?, `note`? |
| `cn-steps` | `kicker`, `title`(2), `steps[3–4]`: `label`?("STEP n"), `title`, `desc`, `point`? |
| `cn-statement` | `kicker`?("KEY MESSAGE"), `title`(3, 핵심어 `*강조*`), `desc`?(2), `foot`?("INSIGHT LEARNING") |

## 5. 줄 길이 (한 줄 최대, 한글 기준 대략값)

생성기(`build-deck.mjs`)는 실측 글자 폭으로 정확히 검사합니다. 아래는 쓸 때 참고할 대략값입니다.
공백과 영문은 한글보다 좁아서 조금 더 들어갑니다.

| 칸 | 최대 | 칸 | 최대 |
|---|---|---|---|
| 표지 제목 (24px) | 약 10자 | 도입 제목 (24px) | 약 11자 |
| 확장 카드 제목 (20px) | 약 13자 | feature 제목 (20px) | 약 13자 |
| statement 제목 (24px) | 약 10자 | closing 결론 (20px) | 약 13자 |
| 표지 소제목 · feature 설명 (14px) | 약 18자 | 도입 소제목 · 포인트 문구 (12px) | 약 23자 |
| compare 칸 (11px) | 약 9자 × 2줄 | FAQ 말풍선 (10px) | 약 17자 × 2줄 |
| split 체크 (11px) | 약 22자 | summary · steps 설명 (9px) | 약 25자 |
| checklist 항목 제목 (14px) | 약 15자 | checklist 설명 (8px) | 약 25자 × 2줄 |
| grid 타일 제목 (13px) | 약 7자 | grid 타일 설명 (9px) | 약 11자 × 2줄 |
| story 본문 (12px) | 약 80자 전체 | | |

## 6. 사진 고르기

- Unsplash **무료 사진(Unsplash License)만** 씁니다. "Unsplash+" 표시가 있는 사진은 쓰지 않습니다.
- 카드 내용을 그대로 보여주는 장면을 고릅니다. 사람, 업무 현장, 기기처럼 구체적인 장면이 좋습니다. 추상 배경이나 일러스트는 피합니다.
- **글자가 올라가는 자리가 비어 있어야 합니다.**
  - `cn-cover`: 아래 1/3 (테이블, 바닥 등 단순한 영역)
  - `cn-intro`: 위 1/2 (벽, 천장, 하늘)
  - `cn-closing`: 가운데 (단순한 패턴, 하늘, 건물 외벽)
- 풀블리드 카드(cover/intro/closing)에서 가로 사진은 좌우만 잘립니다. 그래서 세로 위치(`position` 의 두 번째 값)는 효과가 없습니다. 얼굴이 글자와 겹치면 위치를 조정하지 말고 **사진을 바꾸거나 다른 사진 카드와 맞바꿉니다**. 가로 위치(`"30% 50%"`)로는 피사체를 좌우로 옮길 수 있습니다.
- 한 덱 안에서 같은 사진가나 비슷한 구도가 연달아 나오지 않게 합니다.
