---
name: generic-redesign
description: >
  Turns client-specific Insightlearning proposal decks (PPTX / PPT / PDF / DOCX) into client-neutral
  "범용" course decks redesigned in the Insightlearning theme, then verifies, renders and delivers
  `<원본명>_범용.pptx`. Removes client names, sites, dates and client-only industry context,
  turns schedule/headcount into "협의", rebuilds the budget as unit price + 산정 방식, keeps instructor
  records, and reports source data issues. Use when the user hands over one or more proposal files and
  says "범용으로 바꿔", "범용 과정으로 만들어", "고객사 이름 빼고 리디자인", "범용본", or invokes
  /generic-redesign. Runs on top of the /slide pipeline (native SVG → PPTX).
---

# /generic-redesign — 고객사 제안서 → 범용 과정 덱

> 상위 규칙: 루트 `CLAUDE.md` (1280×720, 단일 액센트, GM 라인, 직렬 실행, **SVG 생성은 메인 에이전트가 한 덱씩 순차**, 후처리 3단계 개별 호출). 이 스킬은 그 위에서 범용화 + 리디자인을 반복 가능한 절차로 묶는다.
> 테마 전제: 활성 테마가 `insightlearning`이어야 한다 (`references/theme-active.json`의 preset 확인; 아니면 `init_theme.py --activate insightlearning` 여부를 사용자에게 묻는다).

## 입력

- 원본 파일 경로 1개 이상 (사용자가 첨부/나열).
- 납품 폴더: 기본 `~/OneDrive/바탕 화면/김주영 업무폴더/범용과정_리디자인`, 그 폴더가 없는 환경(클라우드)은 `output/_deliver/` (환경변수 `GENERIC_REDESIGN_DST` 또는 사용자 지정이 우선).
- 엔딩 연락처: `contacts.local.txt` 또는 `GR_CONTACTS` (커밋 금지 — generic-rules §4). 클라우드 세션처럼 둘 다 없으면 시작할 때 사용자에게 한 번 묻고 `GR_CONTACTS="…|…"`를 빌드 명령 앞에 붙인다.
- 묻지 않고 진행: 범용화 규칙(`references/generic-rules.md`)은 승인된 기본값. 사용자가 "고객사 버전도" 등 다른 요구를 할 때만 확인.

## 절차 (덱마다 순서대로, 덱 사이도 직렬)

### 0. 작업 폴더 + 추출 (한 번에 전부)

```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/generic-redesign/scripts/extract_source.py output/_generic_work \
    b2b="<원본1.pptx>" ehs="<원본2.pdf>" ...
```
- 짧은 ASCII stem(`b2b=`)을 붙인다. 원본은 사본으로 작업 — 원본 이동·수정 금지.
- 산출: `<stem>.md`(텍스트), `<stem>_files/`(사진), `r_<stem>/gridN.png`(원본 렌더). **md와 grid 이미지를 둘 다 읽고** 구조·표·사진 위치를 파악한다.
- 강사 사진: `<stem>_files/`에서 골라 필요하면 PIL로 3:4 크롭 → `output/_generic_work/img/inst_<이름>.jpg`.

### 1. 범용화 패스 (덱별 메모)

`references/generic-rules.md`를 적용해 덱마다 짧은 메모를 만든다 (대화 안에서 정리, 파일 불필요):
- 지울 것 / 일반화할 표현 목록, 새 과정명·파일명(`…_범용.pptx`)
- 예산 산식 검산 결과 (불일치·VAT 표기 오류 → flag)
- 원본에 없어 요약으로 구성할 부분 (→ 슬라이드 주석 + flag)

### 2. 빌드 스크립트 작성 → 실행

- `examples/`에서 구조가 가장 비슷한 예시를 골라 `output/<topic>_generic/build.py`로 복사·수정 (첫 실행 시 `init()`이 프로젝트를 만든다 — 먼저 `output/_generic_work/<topic>_build.py`에 써도 된다).
- 블록·좌표·함정: `references/layout-kit.md`. 원본 구성을 존중하되 필요하면 페이지를 나누거나 합친다 (/slide-plan 방식의 구성 재편).
- 스크립트 구성: `init(P, images)` → `plan(P, …rows…)` (R1–R5 검증 통과 필수; role 허용값은 kit.plan docstring) → `cover` → `page(...)` × N → `ending` → `notes(P, …)` → `checkall(P)`.
- 실행: `.claude/skills/slide/scripts/_py.sh output/<topic>_generic/build.py` → checkall 출력에서 ERROR 0, 의미 있는 WARN은 수정.
- 헤드라인 = so-what 문장, GM = 편집적 한 줄(제목 재진술 금지), 합니다체.

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
(export는 장수가 많으면 `run_in_background`)

### 4. 검증·렌더·납품

```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/generic-redesign/scripts/finish.py <project> "<이름>_범용.pptx"
```
- verify_deck PASS가 아니면 납품하지 않는다.
- **`output/<project>/_pptx_render/gridN.png`를 전부 직접 본다.** 넘침·겹침·잘림·어색한 줄바꿈·빈 공간이 있으면 build.py 수정 → 2–4단계 재실행 (finish가 같은 이름으로 덮어씀).
- 출력의 `render:` 줄로 렌더러를 확인한다 (`powerpoint` / `libreoffice` / `svg-approx`). svg-approx면 보고에 "최종 서체 확인은 PowerPoint에서" 한 줄을 넣는다.
- PowerPoint COM은 동시에 두 개 돌리지 말 것 (export와 finish 렌더가 겹치면 대기 후 실행).

### 5. 보고 (모든 덱 완료 후)

- 납품 폴더 + 덱별 파일명·장수 표.
- 범용화로 바뀐 것 요약 (고객사명 제거, 협의 처리, 예산 방식).
- **확인 필요 flag** (generic-rules §7): 산식 불일치, VAT 표기, 지어낸/요약 구성 부분, 수치 충돌, 연락처 불일치, 예산 미포함 사유.

## 파일

| 경로 | 내용 |
|---|---|
| `scripts/extract_source.py` | 원본 → md + 사진 + 페이지 렌더/그리드 |
| `scripts/ilkit/kit.py` | `init` · `plan` · `notes` · `checkall` + 블록 (`from kit import *`) |
| `scripts/ilkit/sv.py` · `blocks.py` · `planlib.py` | SVG 기본 요소·셸 / 표·셰브론·시간표 / plan·spec 작성 |
| `scripts/finish.py` | verify → zip 검사 → 렌더 → 납품 |
| `scripts/render.py` | 렌더러 선택: PowerPoint → LibreOffice → SVG 근사 렌더 (PyMuPDF) |
| `references/generic-rules.md` | 범용화 규칙 (승인본) |
| `references/layout-kit.md` | 셸 좌표 · 블록 카탈로그 · 함정 · 페이지 패턴 |
| `examples/*.py` | 검증된 빌드 스크립트 3종 (6H 단일 / 3과정 묶음 / 18장 프로그램) |

## 호스트 (로컬 PC · Claude Code 클라우드 세션)

같은 절차가 두 환경에서 돈다. 렌더러와 납품 위치만 자동으로 바뀐다 (`scripts/render.py`).

| | 사용자 Windows PC | 클라우드 세션 (claude.ai/code, Linux) |
|---|---|---|
| 의존성 | `.venv` 이미 설치 | 시작 시 `pip install -r requirements.txt` (python-pptx · svglib · PyMuPDF · Pillow) |
| 원본 렌더 (extract) | PowerPoint | PDF는 PyMuPDF. PPTX는 LibreOffice가 있으면 사용, 없으면 텍스트·사진만 → md와 `<stem>_files/`로 구조 파악, 사용자에게 알림. `.ppt`는 LibreOffice 없으면 .pptx/.pdf로 다시 요청 |
| 완성본 렌더 (finish) | PowerPoint (정확) | LibreOffice → 없으면 `svg-approx` (svg_final을 PyMuPDF로 렌더: 한글이 더 넓은 대체 폰트 → 넘침·겹침 판단용, 최종 서체 확인은 PowerPoint에서 하라고 보고) |
| 납품 | `~/OneDrive/바탕 화면/김주영 업무폴더/범용과정_리디자인` | `output/_deliver/` — 세션의 파일 전달 기능으로 사용자에게 넘기고 경로를 알려 준다 (output/는 git 무시 대상이라 커밋되지 않음) |
| 사진 소스 | 원본 PPTX 추출 | 동일 (사용자가 업로드한 파일 기준) |

- 클라우드에서 LibreOffice 설치가 가능하면(`apt-get install -y libreoffice-impress`) 렌더 품질이 PowerPoint에 가까워진다 — 설치 실패는 무시하고 svg-approx로 진행.
- `finish.py --no-render`는 렌더를 완전히 건너뛴다 (권장하지 않음).
- Codex 미러에는 포함하지 않는다 (`sync_codex_mirror.py` 제외 목록).
