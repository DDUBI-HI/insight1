# 레이아웃 레퍼런스 (deck.yaml)

## 스펙 구조

```yaml
lock_content: false               # true = 기존 덱 내용 고정 리디자인 (GM·라벨·번호 자동 추가 없음)
project: privacy_basic            # output/<project>/ 폴더 이름 (영문·숫자·_)
file: 개인정보보호_기본교육.pptx   # finish.py에 넘길 납품 파일명
course: 개인정보보호 기본교육      # 헤더 왼쪽 라벨 (모든 장)
brand: INSIGHTLEARNING            # 밴드 왼쪽 작은 브랜드 ("" 이면 생략)
pages:
  - layout: statement             # 아래 19종 중 하나
    section: 1-1. 개인정보 정의    # 「 」 섹션 라벨 (선택)
    title: 개인정보|란?            # 투톤 제목: "초록 | 네이비" (공백 없는 | 는 붙여 씀)
    gm: …                         # 콘텐츠 장 필수 — 하단 결론 한 줄
    notes: …                      # 강사 대본 (PPT 슬라이드 노트로 들어감)
    illust: thinking              # 일러스트 키 / auto / none
    …                             # 레이아웃별 필드
```

목록 항목은 세 가지로 쓸 수 있다: `"제목"` · `[제목, 설명]` · `{title: 제목, desc: 설명, icon: …}`.
`?` `,` `:` 가 든 문장은 `[ ]` 흐름 표기 안에서 깨지므로 블록 표기나 따옴표를 쓴다.

## 내용 → 레이아웃 선택표

| 내용의 모양 | 레이아웃 | 원본 템플릿 |
|---|---|---|
| 과정 시작 | `cover` | p.1 |
| 차시 목차 2–6개 | `agenda` | p.2 |
| 큰 단원 전환 | `section` | (추가) |
| 정의·핵심 한 문장, 질문 던지기 | `statement` | 영상 예시 화면 |
| 순서 없는 요점 2–5개 | `points` | (추가) |
| 주장 하나 + 근거 2–4개 | `icon_list` | p.3 |
| 유형·요소 2–4개 병렬 | `cards` | p.4, p.16 |
| 핵심 수치 2–4개 | `stats` | p.6 |
| 추이·비교 수치 | `chart` | p.5 |
| 3–5단계 과정 | `flow` | p.7 |
| A vs B (나쁜 예/좋은 예) | `compare` | p.9 |
| 전 → 후 변화 | `before_after` | p.10 |
| 위계·우선순위 3–5단 | `pyramid` | p.11 |
| 기준표·체크리스트 | `table` | p.12 |
| 실천 행동 2–3개 (그림으로) | `illust_cards` | p.13 (사진 → 일러스트 교체) |
| 핵심 원칙 4개 정리 | `hub` | p.14 |
| 자주 묻는 질문 | `qa` | p.15 |
| 실제 화면·사진 따라하기 | `image` | (추가) |
| 마무리·다음 차시 | `ending` | p.17 |
| 단원 마무리 (번호 + 단원명 + 감사합니다) | `ending` + `no` | (추가) |
| 단순 목록 (불릿 · ◆ · ✓) | `bullets` | (추가) |
| 소제목 + 설명 상자 1–3개 / 좌우 2단 | `panels` | (추가) |
| 유형·분류 4–6개 타일 | `grid` | (추가) |
| 정의 + 해당 항목 키워드 | `keywords` | (추가) |
| 퀴즈 (보기형 · O/X, 문제 장 → 정답 장) | `quiz` | (추가) |

## 레이아웃별 필드

| 레이아웃 | 필드 (굵게 = 필수) | 개수·기본값 | 파일 역할 |
|---|---|---|---|
| `cover` | **title**, eyebrow, subtitle, meta, illust | illust 기본 `presenter` · 제목 투톤은 두 줄(초록 줄 / 네이비 줄) | cover (GM 없음) |
| `agenda` | **items**, title, illust | 2–6개 · title 기본 `강의 \| 순서` · illust 기본 `book` | chapter (GM 없음) |
| `section` | **title**, no, label, desc, items, illust | `no` 기본 1 → "PART 01" (label로 변경) · items = 단원에서 다룰 내용 불릿 · illust 기본 auto | chapter (GM 없음) |
| `statement` | **highlight**, lines, body, title, **gm**, illust | lines 1–3줄(28px), highlight 1–2줄(초록 밑줄), body ≤4줄 · 일러스트 없으면 가운데 정렬 | content |
| `points` | **items**, title, **gm**, illust, color | 1–5개 `[제목, 설명]` · color `series`(기본)/`green` | content |
| `icon_list` | **items**, headline, title, **gm** | 2–4개 `{icon, title, desc}` · headline은 왼쪽 큰 문장(투톤) · title 없으면 위쪽부터 사용 | content |
| `cards` | **items**, title, **gm** | 2–4개 `{title, desc, icon?}` · icon 있으면 번호 대신 아이콘 | content |
| `stats` | **items**, title, **gm** | 2–4개 `{label, value, desc}` | content |
| `illust_cards` | **items**, title, numbered, **gm** | 2–4개 `{illust?, title, desc}` (4개 = 2×2) · illust 없으면 제목으로 자동 선택 · numbered 기본 켜짐 | content |
| `flow` | **items**, title, **gm** | 3–5개 `{icon, title}` · 원 안에는 짧은 제목만 (설명은 notes로) | content |
| `compare` | **left**, **right**, title, vs, **gm** | 각 `{title, items[≤5]}` · 왼쪽 = 나쁜/이전 쪽 | content |
| `before_after` | **left**, **right**, title, **gm** | 각 `{title, items[≤5]}` | content |
| `pyramid` | **items**, title, **gm** | 3–5개 `[제목, 설명]` · 첫 항목이 꼭대기 | content |
| `hub` | **items**, headline, title, **gm** | 정확히 4개 `[제목, 설명]` · headline 가운데(투톤) | content |
| `qa` | **rows**, q_title, a_title, title, **gm** | ≤4행 `{q, a}` | content |
| `chart` | **labels**, **values**, kind, unit, max, highlight, points, source, title, **gm** | kind `line`(기본)/`bar` · highlight 기본 마지막 값 · points ≤3 | content |
| `table` | **header**, **rows**, highlight_col, title, **gm** | ≤6행 · 열 폭은 글자 길이로 자동 | content |
| `image` | **src**, fit, caption, points, title, **gm** | src는 deck.yaml 기준 상대경로/절대경로 · fit `meet`(기본)/`cover` · points ≤3 | content |
| `bullets` | **items**, heading, marker, note, stamp, stamp_at, size, label_split, title | ≤8개 · marker `dot`(기본)/`diamond`/`check` · 글자 크기 항목 수로 자동(22→18) · "라벨: 내용"은 라벨 굵게 · stamp = 기울어진 벌칙 도장 줄 목록 | content |
| `panels` | **panels**, cols, illust, stamp, title | panels `[{heading, lines[], items[], note}]` · cols 1(세로, 기본)/2(좌우) · 글자 크기 19→15 자동 맞춤 · illust는 cols 1일 때만 | content |
| `grid` | **items**, title | 2–6개 `{no, title, desc}` · 3·5·6개는 3열 | content |
| `keywords` | **chips**, definition, illust, title | definition `{heading, text}` 네이비 상자 · chips 문자열 목록 | content |
| `quiz` | **question**, options, answer, reveal, explain, illust, title | options `["1. …", …]` · answer = 정답 번호(정답 장에서만) · 보기 없이 reveal `X`/`O` + explain = O/X 정답 장 · illust 기본 `thinking` | content |
| `ending` | title, subtitle, desc, lines, no, illust | title 기본 `감사합니다` · `no` 있으면 단원 마무리(큰 번호 + 단원명) · illust 기본 `trophy` | ending (GM 없음) |

## 아이콘

`icon:` 값은 `assets/icons/tabler-outline/<name>.svg` 이름 (2px 라인). 찾기: `grep <키워드> assets/icons/icons_index.txt`.
자주 쓰는 것: `target filter shield-lock lock user users bulb book checklist chart-line chart-bar clock calendar
message-circle search alert-triangle download database share trash pencil bolt refresh flag device-laptop`.
없는 이름은 `point`로 바뀌고 빌드가 경고한다.

## 글자 맞춤

모든 텍스트는 Pretendard 실제 글자 폭으로 줄바꿈·축소된다. 정해진 줄 수를 넘으면 `[WARN] text too long` —
문장을 줄이거나 notes로 옮긴다. 제목은 30px까지 줄어들고, 그래도 넘치면 카드 밖으로 나가 `[ERROR]`가 된다.
