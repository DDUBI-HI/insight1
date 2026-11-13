---
name: edu-video
description: >
  Builds background slide decks for Insightlearning online lecture VIDEOS — the instructor is keyed in on
  the right, so the right 30% of every slide stays empty and the bottom band is kept free for captions.
  Low-vision rules are built in: no text under 28px (21pt), body 32px (24pt), contrast of 6.6:1 or higher,
  emphasis never carried by colour alone. Uses modern navy line-art illustrations in place of stock photos
  and clip-art. Takes the user's lecture content (script, outline, Word/PDF/PPT) → content YAML →
  native editable PPTX with the narration in speaker notes. Use when the user says
  "교육 영상 PPT", "영상 배경 슬라이드", "강사 합성용 PPT", "이러닝 영상 슬라이드", "내용 넣었어 PPT로 만들어줘"
  (for a lecture video), or invokes /edu-video.
---

# /edu-video — 교육 영상 배경 PPT

> 상위 규칙: 루트 `CLAUDE.md`. 1280×720, 단일 액센트, 이모지 금지, 네이티브 SVG→PPTX, 후처리 3단계를 각각 별도 호출로 실행한다.
> 디자인 규칙의 정본은 `references/design-system.md`이고 PDF 판은 `design-system.pdf`다. 입력 형식은 `references/content-format.md`.
> 테마 전제: 활성 테마가 `insightlearning`이어야 한다 (`.claude/skills/slide/references/theme-active.json`).

## 무엇이 다른가 (/slide 대비)

- 오른쪽 30%(x ≥ 896)는 **강사 영역**이다. 비워 두고 `stage: tint`이면 연한 네이비 면을 깐다.
- 하단 y 644–720은 **자막 안전 영역**이다. 그래서 GM(핵심 한 줄)은 y 568–628 띠에 둔다. 빌더가 `<project>/.gm_band`를 써서 verify_deck이 이 띠를 인식한다.
- **글자 크기 하한은 28px(21pt)이다** (저시력 학습자 배려). 본문 32px, 제목 44px.
- SVG는 Claude가 손으로 그리지 않는다. `scripts/build_deck.py`가 YAML에서 레이아웃 17종을 결정적으로 생성한다. 메인 에이전트가 직렬로 실행하므로 "sub-agent 위임 금지" 규칙을 지킨다.

## 절차

### 0. 처음 한 번 (클라우드 세션 포함)
```bash
pip install -r .claude/skills/slide/requirements.txt
```

### 1. 원고 → YAML
- 사용자의 원고를 화면 단위로 나눈다. 한 화면에 한 메시지, 항목은 4개까지, 항목당 2줄까지.
- 화면마다 레이아웃을 고른다(`design-system.md §7`). 같은 계열이 3장 넘게 이어지지 않게 섞는다.
- `key`(핵심 한 줄)는 반드시 쓴다. 제목을 반복하지 않는 so-what으로 쓴다. `say`(강의 원고 → 노트)에는 화면의 핵심 문구를 넣는다.
- 원고에 퀴즈가 없으면 만들지 않는다. 사용자가 원하면 `quiz` + `answer`를 쓴다.
- 일러스트는 화면 주제에 맞춰 라이브러리에서 고른다. 원본의 스톡 사진·클립아트·회색 목업은 쓰지 않고 교체한다(`design-system.md §6`). 사용자가 준 시스템 캡처만 `screen.image`로 넣는다.
- 저장 위치: `output/<project>/content.yaml` (output/은 git 무시 대상 — 고객 원고 보호).
- 법령·수치는 원고를 그대로 쓴다. 고친 부분이나 확인이 필요한 부분은 보고에 적는다.

### 2. 빌드
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/edu-video/scripts/build_deck.py output/<project>/content.yaml
```
- `FIT ERRORS`가 나오면 YAML을 고친다(줄이기·나누기·레이아웃 바꾸기). 내용을 자르는 방식으로 우회하지 않는다.
- 통과하면 SVG, `slide_plan.json`(educational, R1–R5 검증), `notes/total.md`, `.gm_band`가 생긴다.

### 3. 후처리 (각각 별도 bash 호출 — 묶지 말 것, 추가 플래그 금지)
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/total_md_split.py output/<project>
```
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/finalize_svg.py output/<project>
```
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/svg_to_pptx.py output/<project> -s final
```

### 4. 검증·렌더·납품
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/edu-video/scripts/finish.py <project> "<파일명>.pptx"
```
- verify_deck이 PASS가 아니면 납품하지 않는다.
- `output/<project>/_pptx_render/grid*.png`를 **전부 직접 본다.** 넘침·겹침·어색한 줄바꿈이 있으면 YAML을 고치고 2–4단계를 다시 실행한다.
- LibreOffice 렌더는 한글과 숫자·문장부호 사이에 여백을 더 넣고, 줄바꿈 없는 텍스트 상자를 조금 옮겨 그린다. PowerPoint에서는 생기지 않는 현상이다. 판단할 것은 넘침과 겹침이다.
- 납품: 클라우드는 `output/_deliver/` → 세션 파일 전달로 넘긴다.

### 5. 보고
- 파일명·장수, 레이아웃 구성 요약, 바꾼 이미지·일러스트, 원고에서 줄이거나 나눈 부분, 확인할 사항(법령·수치).

## 파일

| 경로 | 내용 |
|---|---|
| `references/design-system.md` | 정본 규칙 (화면 구조·타이포·접근성·컬러·일러스트·레이아웃·편집 가이드) |
| `references/content-format.md` | YAML 입력 형식 |
| `design-system.pdf` | 디자인 시스템 PDF (사람이 보는 판) |
| `scripts/build_deck.py` | YAML → SVG + plan + notes |
| `scripts/evkit/ev.py` | 토큰 · 줄바꿈 · 셸 · 레이아웃 17종 |
| `scripts/evkit/illust.py` | 라인 일러스트 라이브러리 17종 (네이티브 셰이프, 라이트/네이비) |
| `scripts/evkit/evcheck.py` | 강사 영역·자막 영역 침범, 28px 하한 검사 |
| `scripts/finish.py` | verify → 렌더 → 납품 |
| `scripts/make_design_pdf.py` | 견본 덱 + 규칙 → `design-system.pdf` |
| `examples/privacy_basics.yaml` | 견본 21장 (레이아웃 17종 전부) |
