# Layout kit — `scripts/ilkit/kit.py`

Insightlearning 셸 좌표와 재사용 블록. 모든 블록은 SVG 조각 문자열을 반환하고 `page(fname, label, title, gm, num, body)`에 넣는다.

## 셸 좌표 (1280×720, 변경 금지)

| 요소 | 좌표 |
|---|---|
| 섹션 라벨 `NN \| 섹션명` | x=56, y=62, 24/300 |
| 이중 네이비 룰 | y=72–78 |
| 헤드라인 (so-what 문장) | 중앙, y=128, 29.6/800 — 한 줄 ≤ 약 34자 |
| lead (선택) | y=158 |
| 콘텐츠 영역 | x=96–1184, y=184–632 (각주는 y≈644–656) |
| GM (governing message) | y=680, 15.2/700 #595959 — 제목 재진술 금지, 편집적 so-what |
| 페이지 번호 | y=696 |

## 블록 카탈로그

| 함수 | 용도 | 크기 |
|---|---|---|
| `cover(eyebrow, l1, l2, lead, foot)` | 표지 (파일명에 `cover`) | 셸 |
| `ending(accent, foot, fname)` | 엔딩 (파일명에 `ending`) | 셸 |
| `info_panel(rows, eyebrow, x, w)` | 왼쪽 네이비 과정 정보 패널 (`[(라벨, 값|[줄])]`) | 기본 96,184 400×448 |
| `numlist(X, top, items, width, gap, eyebrow)` | 01/02/03 번호 목록 (`[(제목, 설명)]`) | gap 70–88 |
| `bullets(X, y, items, fs, gap)` | 점 목록 | |
| `chevrons(mods)` | 3–5단 셰브론 모듈 흐름 (label, name, icon, tag, core[2], method, out[2]) | y=192–550 |
| `tablerows(cols, head, rows, top, rh, hl)` | 네이비 라벨열 표 → `(svg, bottom_y)` | rh 56–96 |
| `timetable(rows, hl, top, rh)` | 시간표 `(시간, 소요, 제목, 내용, 방식)` | 96–1184 |
| `modrows(rows, top, lh, pad, hl)` | 모듈 상세표 `(M1, 모듈명, [("", 줄)], 방법, 시간)` | 4모듈 ≈ 350px |
| `modgrid(mods, rows, hl)` | 2열 모듈 비교 | |
| `qgrid(Q, hl)` | 2×3 질문 카드 (사전 설문/점검) | |
| `cards(items, top, h, hl)` | N열 네이비 헤더 카드, body 함수 콜백 | |
| `profile_one(img, name, title, now, left, right, tag)` | 강사 1인 프로필 (사진 + 2열) | |
| `roster(rows, …)` | 강사 다수 비교표 | |
| `budget_unit(rows, hero, hero_label, stats, formula, note)` | 범용 예산 (단가·산정 방식) | 전체 |
| `tagline(x, y, "[태그] 내용")` | 네이비 태그 + 본문 (폭 자동 계산) | |
| `wo(svg, op)` | 흰색 요소에 fill-opacity | |
| `text_w(s, fs)` / `wrap(s, n)` | 폭 추정 / 줄바꿈 | |
| `ic(name, x, y, s)` | Tabler 아이콘 — `assets/icons/tabler-outline/<name>.svg` 존재 확인 후 사용 | |

## 실전에서 배운 함정

- **스카이 `#58CCFF`는 표지·엔딩에만**. 콘텐츠 페이지에서 강조는 네이비 `#012281` 또는 소프트 `#E0EDF3` 배경 하나.
- 텍스트 안 `&` → `&amp;` (안 하면 export 실패). `<`, `>`도 이스케이프.
- 셸 파일명에 `cover`/`ending`이 없으면 verify_deck이 GM 누락 콘텐츠로 판정.
- `▸` 같은 특수 기호는 Pretendard에 없을 수 있음 → `→`, `·` 사용. 원문자 ①–⑬은 렌더됨.
- 줄 길이: 12.8px 본문 ≈ 폭/12.8 한글자, 13.6px ≈ 폭/13.6. 카드 폭 260이면 12.8px 약 17자. 넘치면 `wrap()`으로 2–3줄, 박스 높이도 같이 늘린다.
- 한 페이지 강조(E0EDF3)는 1개 행/카드만.
- 모듈 상세처럼 텍스트가 많은 페이지는 F8F8F8 카드 배경을 깔아 "text-led" 경고를 줄인다.
- 헤드라인이 길면 1줄을 넘음 → 34자 안쪽으로.
- 원본 사진은 `extract_source.py`가 만든 `<stem>_files/`에서 고르고, 필요하면 PIL로 얼굴 기준 3:4 크롭해 `WORK/img/`에 저장.

## 페이지 구성 패턴 (검증된 것)

- **6H 단일 과정 (8장)**: 표지 → 과정 개요(info_panel + 대상·목표 numlist) → 모듈 흐름(chevrons) → 모듈 상세(tablerows/timetable) → 사전 준비·설문(qgrid) → 강사(profile_one) → 예산(budget_unit) → 엔딩. → `examples/example_b2b_6h.py`
- **과정 3종 묶음 (8장)**: 표지 → 과정 구성 카드 3열 → 과정별 상세(info_panel + 개요·목표·모듈) ×N → 예산 → 엔딩. → `examples/example_three_courses.py`
- **다개월 프로그램 (18장)**: 필요성 → 사례표 → 설계 원칙 2×2 → 운영 환경 → 운영 모델 → 월별 파일럿 → 모듈 상세 ×3 → 부가 세션 → 연계 → 프로세스 → 역할분담표 → 사전 점검 → 강사 → 예산 → 엔딩. → `examples/example_program_18p.py`
- **카탈로그 (20+장)**: 개요 → 전체 과정 맵(레벨 3열) → 직무별 로드맵(그리드) → 과정 상세 ×N(상단 목표 스트립 + modrows) → 예산.
