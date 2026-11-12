# deck.yaml 형식 — lecture-slide

사용자가 준 강의 내용을 이 형식으로 옮기면 `build.py`가 바로 SVG → PPTX 파이프라인에 넣는다.
`.json`도 같은 구조로 받는다. 전체 견본: `examples/sample_deck.yaml` (18개 레이아웃 전부 사용).

## 최상위

```yaml
project: privacy_basic        # output/<project>/ (ASCII, 짧게)
title: 개인정보보호 기본 교육   # 덱 제목 (plan·spec용, eyebrow 기본값)
brand: INSIGHTLEARNING        # 표지·간지·엔딩 하단 띠 + 콘텐츠 왼쪽 아래 (빈 값 가능)
footer: INSIGHTLEARNING       # (선택) 콘텐츠 페이지 왼쪽 아래만 따로 바꿀 때
top_left: ONLINE LECTURE      # 표지·간지·엔딩 상단 왼쪽 라벨
top_right: 2026 개인정보보호 교육 # 상단 오른쪽 라벨 (존 오른쪽 끝 x=848에 정렬)
slides: [...]
```

## 모든 콘텐츠 슬라이드 공통

| 키 | 필수 | 설명 |
|---|---|---|
| `layout` | ✓ | 아래 18종 또는 `cover` / `chapter` / `ending` |
| `title` | ✓ | 페이지 제목 (≈ 22자, 넘으면 자동 축소 → 경고) |
| `gm` | ✓ | 하단 한 줄 핵심 메시지 — 제목 재진술 금지, ≈ 34자 이내 |
| `eyebrow` | | 제목 위 작은 줄. 생략하면 직전 chapter의 `label` → 덱 `title` |
| `lead` | | 제목 아래 설명 한 줄 (본문이 34px 내려감) |
| `notes` | | 발표자 노트 = 강의 대본. 생략하면 `제목. GM` |

이미지 값은 deck 파일 기준 상대경로 또는 절대경로. `null`/빈 값/없는 파일 → 플레이스홀더(PPT에서 교체).

## 셸

```yaml
- layout: cover
  badge: 법정 의무교육            # 선택
  subtitle: 모든 임직원이 꼭 알아야 할  # 선택, 가는 글씨
  title: 개인정보보호 기본 교육
  info: [강사 홍길동, 인싸이트러닝, 약 30분]   # 선택, 세로선으로 구분

- layout: chapter
  label: CHAPTER 01             # 배지 문구 — 이후 페이지 eyebrow 기본값
  title: 개인정보의 정의
  sub: 어디까지가 개인정보일까요?  # 선택

- layout: ending
  badge: THANK YOU
  subtitle: 오늘 배운 습관 하나로    # 가는 줄 (선택)
  title: 안전한 일터를 만듭니다      # 굵은 줄
  contacts: [인싸이트러닝, insighthrd.com]   # 선택 — 실제 연락처는 커밋 금지(output/만)
```

## 레이아웃별 필드

```yaml
- layout: statement            # 핵심 문장 강조
  lines: [사망자의 정보라도, 유족과의 관계를 알 수 있는 정보는]
  emphasis: 유족의 개인정보에 해당   # accent + 밑줄
  note: "※ 개인정보 보호법 제2조"   # 선택
  icon: bulb                   # 선택 (Tabler outline 이름)
  align: center                # center | left

- layout: bullets
  heading: 이것만은 꼭 기억하세요   # 선택
  numbered: true               # false면 점
  items: [문장, 문장]            # 또는 [{title: …, desc: …}]

- layout: text_image
  image: img/photo.jpg
  tags: [민감정보, 고유식별정보]
  heading: 선택 소제목
  text: 본문 문단 (자동 줄바꿈)

- layout: two_col
  cols: [{title: …, image: …, text: …}, {title: …, image: …, text: …}]

- layout: stats                # desc 하나라도 있으면 카드형(p7), 없으면 아이콘 패널(p6)
  items: [{label: 내부자 과실, value: 62, unit: "%", icon: user-exclamation, desc: 선택}]

- layout: cards                # 3개 (4개 이상이면 points로 자동 전환)
  items: [{icon: target, title: 목적 명확화, desc: …}]

- layout: points               # 2–4개, POINT 01… 자동
  items: [{icon: lock, title: 화면 잠금, desc: …}]

- layout: keywords             # 정확히 3개, 가운데 강조
  items: [{title: …, desc: …}, {title: …, desc: …}, {title: …, desc: …}]

- layout: chart
  bars: [{label: 교육 전, value: 58}, {label: 교육 후, value: 91}]
  unit: ""                     # 막대 값 뒤 단위 (선택)
  max_value: 100               # 선택 (기본: 자동 눈금)
  heading: 교육 후 달라진 점      # 오른쪽 해설 카드 (items 없으면 차트만 전체 폭)
  items: [문장, 문장, 문장]

- layout: process
  steps: [{title: 고지, sub: 목적·항목 안내}, …]   # 3–4
  result: {title: 적법 수집, sub: 분쟁 예방}       # 선택

- layout: steps
  items: [{icon: file-text, title: 수집, label: STEP 1}]   # label 생략 시 STEP n

- layout: before_after
  quote: "\"인용문\""            # 선택
  labels: [BEFORE, AFTER]       # 선택
  rows: [[전, 후], [전, 후]]

- layout: cause_result
  causes: [원인 1, 원인 2]
  result: 결과 문장

- layout: timeline
  stages: [{label: 즉시, icon: alert-triangle, title: 확산 차단, desc: …}]   # 3–4

- layout: toc
  items: [{title: 개인정보의 정의, desc: 어디까지가 개인정보인가}]   # 3–6

- layout: image_grid
  images: [a.jpg, b.jpg, c.jpg]   # 1–3장

- layout: quiz
  question: 회사 대표 전화번호도 개인정보에 해당한다.
  options: [O, X]               # O/X면 큰 타일, 아니면 번호 보기 목록
  answer: X                     # 선택 — 정답 공개 장. 보기 문자열 또는 1부터 번호
  label: "Q."

- layout: table
  header: [구분, 보유 기간, 파기 방법]
  widths: [1.2, 1, 1.4]         # 열 비율 (선택)
  rows: [[…, …, …], …]
  highlight: 1                  # 강조 행 (1부터, 선택)
```

## 아이콘

`assets/icons/tabler-outline/<이름>.svg`가 있어야 한다 (없으면 경고 + `point`). 자주 쓰는 것:
`bulb target shield-lock lock key mail printer file-text device-laptop share trash filter users user school book clock calendar bell refresh alert-triangle check x chart-bar message-circle question-mark id heart-handshake`
검색: `grep -i <단어> assets/icons/icons_index.txt` 또는 `ls assets/icons/tabler-outline | grep <단어>`.
