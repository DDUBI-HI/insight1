---
name: lecture-slide
description: >
  Builds lecture-VIDEO background decks (강의 영상 배경 PPT) in the Lecture Video design system sampled from the
  공공기관/지자체 template PDF — periwinkle frame, lavender bands, soft cards, Pretendard — with the RIGHT 30% of every
  slide left empty for the composited instructor video. The user pastes lecture content (outline, script, bullet
  notes); Claude maps it to 18 layouts in a deck.yaml, builds native editable PPTX through the /slide SVG pipeline,
  verifies, renders a safe-zone preview and delivers. Use for "강의 영상 PPT", "영상 배경 슬라이드", "강사 합성용
  슬라이드", "교육 영상 PPT 만들어줘", "이 내용으로 강의 슬라이드", or /lecture-slide.
---

# /lecture-slide — 내용 → 강의 영상 배경 PPT

> 상위 규칙: 루트 `CLAUDE.md` (1280×720, 단일 액센트, GM 라인, 이모지 금지, 네이티브 SVG→PPTX, 후처리 3단계 개별 호출).
> 디자인 정본: `DESIGN.md` · 입력 형식: `references/deck-format.md` · 구현: `scripts/lskit.py`.
> 활성 테마(`theme-active.json`)는 바꾸지 않는다 — 이 스킬은 자체 팔레트를 `.theme-color-allow`로 등록한다.

## 핵심 규칙

1. **오른쪽 30 %(x ≥ 896)는 강사 영상 자리 — 배경만, 콘텐츠 금지.** 콘텐츠는 x 56–856, 가운데 정렬은 x=456 기준. `lskit`이 위반을 빌드 실패로 막는다.
2. 모든 콘텐츠 장에 `gm` (하단 한 줄 so-what, 제목 재진술 금지). 셸(cover/chapter/ending)은 제외.
3. 강의 원고 한 단락 = 한 장. 넘치면 나눈다. 본문 ≥ 16px.
4. 대본이 있으면 `notes`에 그대로 넣는다 (녹화용 발표자 노트).

## 절차

### 0. 처음 한 번
```bash
pip install -r .claude/skills/slide/requirements.txt
```
(LibreOffice 렌더용 Pretendard는 `finish.py`가 `fonts/`에서 자동 설치. fonttools·brotli가 없으면 `pip install fonttools brotli`.)

### 1. 내용 → deck.yaml (묻지 않고 진행)
- 사용자가 준 내용을 `output/<project>/deck.yaml`로 옮긴다 (output/은 커밋 안 됨). 형식: `references/deck-format.md`, 견본: `examples/sample_deck.yaml`.
- 구성 기본값: `cover` → (`toc`) → 챕터마다 `chapter` + 본문 장들 → (`quiz`/`bullets` 요약) → `ending`.
- 레이아웃 고르기 (DESIGN.md §7): 정의·핵심 문장 → `statement` · 3개 원칙 → `cards` · 4개 → `points` · 순서 → `steps`/`process`/`timeline` · 전후 비교 → `before_after` · 사례 → `cause_result` · 수치 → `stats`/`chart` · 기준표 → `table` · 확인 문제 → `quiz` (정답 공개는 같은 문제 + `answer`).
- 같은 레이아웃 3장 연속은 피한다 (plan R4). eyebrow에 목차 번호(`1-1. …`).
- 사용자가 안 정한 값: `brand: INSIGHTLEARNING`, `top_left: ONLINE LECTURE`, `top_right: <과정명>`. 수치·사례는 사용자 자료에 있는 것만 — 없으면 지어내지 말고 플레이스홀더 + 보고.
- 이미지: 사용자가 준 파일 경로를 넣는다. 없으면 `null`(플레이스홀더 — PPT에서 그림 바꾸기).

### 2. 빌드
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/lecture-slide/scripts/build.py output/<project>/deck.yaml
```
- `[ERROR]`(safe-zone 위반·gm 누락·잘못된 필드)는 deck을 고쳐 다시. `[WARN]`(제목·GM 길이, 압축된 표 등)도 대부분 문장을 줄여 해결.

### 3. 후처리 (각각 별도 bash 호출 — 묶지 말 것)
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/total_md_split.py output/<project>
```
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/finalize_svg.py output/<project>
```
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/svg_to_pptx.py output/<project> -s final
```
(재빌드 전 `output/<project>/exports/*.pptx`를 지우면 최신 파일 혼동이 없다.)

### 4. 검증·렌더·납품
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/lecture-slide/scripts/finish.py <project> "<과정명>.pptx"
```
- verify_deck PASS가 아니면 납품하지 않는다.
- `output/<project>/_pptx_render/gridN.png`(넘침·겹침·줄바꿈)와 `zoneN.png`(강사 실루엣 오버레이 — 콘텐츠가 가리지 않는지)를 **전부 직접 본다**. 문제가 있으면 deck 수정 → 2–4 재실행.
- 렌더러가 `libreoffice`/`svg-approx`면 문장부호 주변 간격·줄 시작 위치가 PowerPoint와 조금 다르다 → "최종 서체 확인은 PowerPoint에서" 한 줄 보고.
- 납품: 기본 `output/_deliver/` (`--dst` 또는 `LECTURE_SLIDE_DST`로 변경). 클라우드 세션은 파일 전달로 넘긴다.

### 기존 덱 리디자인 — "내용은 그대로, 디자인만" (내용 보존 모드)
사용자가 원본 내용을 한 글자도 바꾸지 말라고 하면 이 모드로 한다.
- 원본(PDF/PPTX)의 텍스트를 화면 기준으로 추출한다 — PDF 추출은 띄어쓰기를 빠뜨릴 수 있으니 글자 간격(≥ 0.22em)으로 공백을 복원해 비교한다. 오타·표기도 원본 그대로.
- `output/<project>/build.py`에서 `K.PRESERVE = True` → `content_page(fname, None, title, None, None, body)`: GM·eyebrow·쪽번호·브랜드 등 원본에 없는 텍스트를 넣지 않는다 (헤더가 위로 당겨지고 본문은 `TOP_COMPACT`부터).
- 사진·스크린샷·이미지로 된 표는 원본 이미지를 xref로 뽑아 그대로 쓴다. 옛 템플릿 장식(클립아트 인형·말풍선 틀·반사)은 새 디자인 요소로 바꾼다. 도형·이미지 안의 글자는 확대해 읽고 실제 텍스트로 옮긴다.
- 빌드 후 원본 각 쪽의 모든 텍스트 줄이 새 SVG에 있는지, 원본에 없는 텍스트가 없는지 자동 대조한다.
- 10장 이상이면 `.standalone`을 두고(slide_plan 생략), 납품은 `finish.py … --preserve-content` (verify의 GM 누락만 허용 — 다른 실패는 그대로 막힌다).

### 5. 보고
장수·레이아웃 구성, 플레이스홀더로 남긴 이미지, 지어내지 않고 비워 둔 수치, 렌더러 종류.

## 파일

| 경로 | 내용 |
|---|---|
| `DESIGN.md` | 디자인 시스템 정본 (세이프존·팔레트·타이포·셸·컴포넌트·레이아웃 18종) |
| `theme.json` | 토큰 JSON (색·글꼴·좌표) |
| `references/deck-format.md` | deck.yaml 형식 |
| `scripts/lskit.py` | primitives(경계 추적) · 셸 · 레이아웃 함수 `L_*` |
| `scripts/build.py` | deck.yaml → svg_output + notes + slide_plan.json + design_spec.md + `.theme-color-allow` |
| `scripts/finish.py` | verify → 렌더(공용 `generic-redesign/scripts/render.py`) → zone 미리보기 → 납품 |
| `examples/sample_deck.yaml` | 27장 견본 (전 레이아웃) |
| `_preview/` | 견본 렌더 (레이아웃 고를 때 참고) |
