# insight1 — 인싸이트러닝 AI 사무실

이 저장소는 여러 업무 도구를 한곳에 모은 공유 작업 공간이다. 각 도구의 상세 규칙은 해당 스킬의 `SKILL.md`가 정본이다.

| 스킬 | 트리거 | 정의 |
|------|--------|------|
| `/cardnews` | `"카드뉴스 만들어줘"` | `.claude/skills/cardnews/SKILL.md` |
| `/generic-redesign` | `"범용으로 바꿔"`, `"범용 과정으로 만들어"`, `"고객사 이름 빼고 리디자인"` | `.claude/skills/generic-redesign/SKILL.md` — 고객사 제안서 → 범용 과정 PPTX |
| `/slide` · `/slide-plan` | `"슬라이드 만들어"`, `"기획부터"` | `.claude/skills/slide/SKILL.md`, `.claude/skills/slide-plan/SKILL.md` |
| `/edu-video` | `"교육 영상 PPT"`, `"영상 배경 슬라이드"`, `"강사 합성용 PPT"` | `.claude/skills/edu-video/SKILL.md` — 원고 → 강사 합성용 영상 배경 PPTX (오른쪽 30% 비움, 저시력 큰 글씨). 디자인 시스템 PDF: `.claude/skills/edu-video/design-system.pdf` |

> ⚠️ **이 저장소는 공개 저장소다.** 고객사 원본·생성된 덱(`output/`)·담당자 연락처(`contacts.local.txt`)는 커밋하지 않는다 (`.gitignore` 처리됨). 결과 파일은 세션의 파일 전달로 사용자에게 넘긴다.

---

## 슬라이드 엔진 (`.claude/skills/slide` 외)

slide-svg에서 가져온 네이티브 SVG→PPTX 파이프라인. 활성 테마는 **Insightlearning** (`.claude/skills/slide/references/theme-active.json`, 네이비 `#012281`, Pretendard).

### 처음 한 번 (클라우드 세션 포함)

```bash
pip install -r .claude/skills/slide/requirements.txt
```
(루트 `requirements.txt`는 카페 알림·카드뉴스용이라 건드리지 않는다.)

### 핵심 제약 (non-negotiable)

- **1280×720 전용**, **단일 액센트**(활성 테마 `colors.accent`만), 그라디언트·글로우 금지
- **모든 콘텐츠 슬라이드 하단에 GM(governing message) 한 줄** — 편집적 so-what, 제목 재진술 금지
- **이모지 금지** — 아이콘은 `assets/icons/tabler-outline` 2px 라인아트만
- **네이티브 SVG→PPTX** — 이미지 플래튼 금지, 편집 가능한 도형 유지
- **직렬 실행**, **SVG 생성은 메인 에이전트가 한 페이지씩** (sub-agent 위임 금지)
- 셸 파일명: 표지 `…cover…`, 엔딩 `…ending…` (verify_deck이 GM 검사에서 제외)
- **교육 영상 덱(`/edu-video`) 접근성 규칙**: 저시력 학습자를 위해 글자 **최소 28px(21pt)**, 본문 32px(24pt), 대비 6.6:1 이상, 색만으로 강조 금지. 오른쪽 30%(x ≥ 896)는 강사 영역, 하단 y 644–720은 자막 영역으로 비운다. GM은 y 568–628 띠에 두고 `<project>/.gm_band`로 verify_deck에 알린다

### SVG 기술 제약 (요약 — 전체는 `.claude/skills/slide/references/shared-standards.md`)

- 금지: `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate>`, `mask`, `<script>`
- `rgba()` 대신 `fill-opacity`, `<g opacity>` 대신 요소별 opacity, 텍스트 `&` → `&amp;`
- 모든 `<text>`에 Pretendard 풀 체인: `Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif`

### 후처리 규율 (각각 별도 bash 호출 — 한 블록에 묶지 말 것, 추가 플래그 금지)

```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/total_md_split.py output/<project>
```
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/finalize_svg.py output/<project>
```
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/svg_to_pptx.py output/<project> -s final
```
- `cp`로 `finalize_svg.py`를 대신하지 말 것, `-s final` 필수.
- 검증: `.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/verify_deck.py output/<project>`

### 렌더·납품 (generic-redesign)

- 렌더러 자동 선택: PowerPoint(Windows) → LibreOffice → SVG 근사 렌더(PyMuPDF, 한글이 넓은 대체 폰트 — 넘침·겹침 확인용)
- 납품: 클라우드 세션은 `output/_deliver/`에 저장 후 사용자에게 전달
- 엔딩 연락처는 `GR_CONTACTS` 환경변수 또는 `contacts.local.txt` — 없으면 사용자에게 묻는다

### 출처

슬라이드 엔진은 slide-svg (MIT, Byungjun Jang) · ppt-master (MIT) · diagram-design (MIT)에서 가져왔다. 고지문: `.claude/skills/LICENSES/`.
