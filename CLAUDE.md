# insight1 — 인싸이트러닝 AI 사무실

이 저장소는 여러 업무 도구를 한곳에 모은 공유 작업 공간이다. 각 도구의 상세 규칙은 해당 스킬의 `SKILL.md`가 정본이다.

| 스킬 | 트리거 | 정의 |
|------|--------|------|
| `/cardnews` | `"카드뉴스 만들어줘"` | `.claude/skills/cardnews/SKILL.md` |
| `/generic-redesign` | `"범용으로 바꿔"`, `"범용 과정으로 만들어"`, `"고객사 이름 빼고 리디자인"` | `.claude/skills/generic-redesign/SKILL.md` — 고객사 제안서 → 범용 과정 PPTX |
| `/slide` · `/slide-plan` | `"슬라이드 만들어"`, `"기획부터"` | `.claude/skills/slide/SKILL.md`, `.claude/skills/slide-plan/SKILL.md` |
| `/ppt-master` · `/ppt-template-fill` · `/native-enhance-pptx` · `/codex-image` | `"ppt-master로 만들어"`, `"이 템플릿에 내용 채워줘"`, `"완성 PPT에 노트·음성 넣어"` | `.claude/skills/ppt-master/workflows/routing.md` 먼저 → 선택된 스킬의 `SKILL.md` (slide-master에서 가져옴, 아래 절 참고) |

> ⚠️ **이 저장소는 공개 저장소다.** 고객사 원본·생성된 덱(`output/`, `projects/`)·담당자 연락처(`contacts.local.txt`)는 커밋하지 않는다 (`.gitignore` 처리됨). 결과 파일은 세션의 파일 전달로 사용자에게 넘긴다.

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

## PPT Master 스킬 (`.claude/skills/ppt-master` 외 3개)

[byungjunjang/slide-master](https://github.com/byungjunjang/slide-master)(MIT, hugohe3/ppt-master 기반)에서 가져온 **별도 엔진**이다. 위 슬라이드 엔진과 규칙이 다르므로 섞지 않는다.

- **라우팅 먼저**: 요청을 받으면 `.claude/skills/ppt-master/workflows/routing.md`부터 읽고 경로를 고른 뒤, 선택된 스킬 문서만 전부 읽는다. 게이트·후처리·검증은 그 문서가 정한다 (예: ppt-master는 `svg_to_pptx.py`에 `-s final`을 쓰지 않는다. 위 "후처리 규율"은 `/slide` 전용).
- **활성 테마 미적용**: ppt-master는 Insightlearning 테마를 자동으로 쓰지 않는다. 브랜드 프리셋(`templates/brands/`)에 Insightlearning이 없으므로 회사 덱은 `/slide`·`/generic-redesign`을 쓰고, ppt-master는 템플릿 채우기·노트/음성 추가·기타 스타일 덱에 쓴다.
- **작업 폴더**: `projects/` (`.gitignore` 처리 — 커밋 금지).
- **처음 한 번**: `pip install -r .claude/skills/ppt-master/requirements.txt` 후 `python3 .claude/skills/ppt-master/scripts/preflight.py`.
- **Codex 연동**: `AGENTS.md`와 `.codex/skills/` 스텁. 어떤 `SKILL.md`든 frontmatter를 고치면 `python3 .claude/skills/ppt-master/scripts/sync_codex_stubs.py`를 다시 돌린다 (안 하면 preflight 실패).
- 선택 도구: OfficeCLI(`npm install -g @officecli/officecli@1.0.135`, 납품 PPTX 검증), Codex CLI(AI 이미지). 없어도 경고만 난다.
- 사용자 문서: `docs/` (설치·FAQ·템플릿 가이드 등, slide-master 원문).

### 출처

슬라이드 엔진은 slide-svg (MIT, Byungjun Jang) · ppt-master (MIT) · diagram-design (MIT)에서, PPT Master 스킬은 slide-master (MIT)에서 가져왔다. 고지문: `.claude/skills/LICENSES/`.
