---
name: program-page
description: >
  Turns an Insightlearning proposal or program file (PPTX / PPT / PDF / DOCX, or pasted text) into the
  homepage "program detail page" image — a 690px-wide vertical page (category + navy course title, info
  pills, goal/target check lists, program box, optional testimonials or worksheet samples), rendered as a
  1380px PNG. The section structure changes with the course type (job-skill, AI practice, teambuilding,
  leadership, solution). Use when the user hands over a proposal/program file and says "상세페이지로 만들어줘",
  "프로그램 소개 이미지", "홈페이지용으로 바꿔줘", "이 형태로 바꿔줘", or invokes /program-page.
argument-hint: <원본 파일…> [유형]
---

# /program-page — 제안서 → 교육 프로그램 상세페이지

원본 제안서·프로그램 파일을 읽어 홈페이지 프로그램 상세 이미지(690px 폭 디자인, 2배 1380px PNG)로 만든다.
**교육 유형에 따라 섹션 구성이 다르다** — 반드시 `references/section-guide.md` 를 읽고 시작한다.

## 먼저 읽을 것
- `references/section-guide.md` — 유형 판별, 유형별 섹션 레시피, 칸별 문구 규칙·길이, 원본→칸 매핑
- `program-page/README.md` — `page.json` 스키마
- `program-page/examples/*.json` — 유형별 정답 예시 5종 (실제 홈페이지 상세 이미지를 그대로 옮긴 것)
- `.claude/skills/generic-redesign/references/generic-rules.md` — 고객사 정보 지우는 규칙

## 절차

### 0. 준비 (세션에서 처음 한 번)
```bash
pip install -r .claude/skills/slide/requirements.txt
```
렌더는 Node + Playwright (`require('playwright')`). 클라우드 세션에는 이미 있다. 로컬 PC에서 없으면 `cd program-page && npm install`.

### 1. 원본 추출
```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/generic-redesign/scripts/extract_source.py output/_pp_work src="<원본 파일>"
```
- 산출: `output/_pp_work/src.md` (텍스트), `src_files/` (원본 속 사진), `r_src/` (페이지 렌더, 가능할 때).
- md 와 페이지 렌더를 둘 다 본다. PPTX 렌더가 안 되는 환경이면 md 와 `src_files/` 로 구조를 파악한다.
- 사용자가 텍스트로 내용을 붙여넣었으면 이 단계는 건너뛴다.

### 2. 유형 판별 → page.json 작성
1. section-guide §1 로 유형을 정하고, §2 레시피와 가장 가까운 예시를 고른다.
2. slug 를 정한다 (영문 소문자-하이픈, 예 `ai-agent-practice`). 폴더: `output/program-page/<slug>/`
3. 예시를 복사해 `output/program-page/<slug>/page.json` 을 쓴다. section-guide §3 문구 규칙, §4 매핑을 따른다.
   - `name` 은 결과 PNG 파일명 (한글 가능, 공백 대신 `_`).
   - 참고자료 이미지는 `src_files/` 에서 골라 `output/program-page/<slug>/img/` 로 복사하고 `"image": "img/…"` 로 건다. 고객사 로고·실명·얼굴이 크게 보이는 사진은 쓰지 않는다.
4. 구조 검사: `node program-page/scripts/build.mjs output/program-page/<slug>/page.json --check`

원본 하나에 과정이 여럿이면 과정마다 slug 를 따로 만든다.

### 2-1. 표지 카드 (사용자가 표지·썸네일을 원할 때)
- `page.json` 에 `cover` 를 넣는다 (스키마: `program-page/README.md`). 상세페이지와 같은 명령으로 `<name>_표지.png`(1080 × 1080)가 함께 나온다.
- 제목은 과정명을 2줄로 끊고 끝에 "과정"을 붙인다 ("Claude 기반\nAI Agent 실무 활용 과정"). 한 줄 11자 안팎.
- 부제는 원본의 한 줄 소개(표지 태그라인)를 2줄로. 한 줄 16자 안팎.
- 사진: 원본 속 과정 대표 사진·삽화를 먼저 쓴다. 없으면 사용자에게 사진을 받거나 Unsplash 무료 사진을 제안한다 (cardnews 스킬의 사진 규칙). 과정끼리 같은 사진을 쓰지 않는다.
- 사진의 인물 얼굴이 위로 잘리면 `position` 을 조정한다 (예 `"center 20%"`).

### 3. 렌더 + 검사
```bash
node program-page/scripts/build.mjs output/program-page/<slug>/page.json
```
- 결과: `output/program-page/<slug>/<name>.png` (1380px 폭), `index.html`, cover 가 있으면 `<name>_표지.png`.
- `△` 경고(줄 꺾임, 빈 이미지, 폭 넘침)는 모두 처리한다: 문구를 줄이거나 `\n` 으로 의미 단위로 끊고, 이미지가 없으면 섹션을 뺀다. 경고 0이 될 때까지 반복 (`--strict` 로 확인 가능).
- **PNG 를 직접 열어 본다**: 줄 바꿈 위치가 어색하지 않은가, 섹션 간격이 고른가, 목표·대상 문장의 끝맺음이 통일됐는가, 고객사 흔적이 남지 않았는가.

### 4. 전달
- PNG 를 사용자에게 보낸다 (여러 과정이면 모두). `output/` 은 커밋하지 않는다 (공개 저장소).
- 여러 장을 묶어 보낼 때는 `output/_deliver/<이름>.zip` 으로 압축하되 **셸 `zip` 명령을 쓰지 않는다**: 한글 파일명에 UTF-8 표시가 빠져 Windows 탐색기에서 빈 압축 파일처럼 보인다. Python `zipfile` 로 묶는다 (한글 이름이면 UTF-8 표시가 자동으로 붙는다):
  ```bash
  python3 -c "import zipfile,sys,os; z=zipfile.ZipFile(sys.argv[1],'w',zipfile.ZIP_DEFLATED); [z.write(f,os.path.basename(f)) for f in sys.argv[2:]]" output/_deliver/<이름>.zip <파일들…>
  ```
- 함께 알릴 것:
  - 유형 판별 결과와 고른 섹션 구성 (한 줄)
  - 원본에서 바꾸거나 묶은 것: 모듈 묶음, 지운 고객사 정보, 줄인 문구
  - **확인 필요**: 원본에 없어 비운 섹션, 원본끼리 충돌하는 수치(교육 시간 등), 추정이 들어간 문구
- 수정 요청이 오면 `page.json` 만 고치고 3단계를 다시 한다.

## 하지 말 것
- `index.html` 이나 PNG 를 손으로 고치지 않는다. 항상 `page.json` → `build.mjs`.
- `program-page/page.css` 를 페이지 하나를 위해 고치지 않는다. 새 블록이 필요하면 사용자에게 제안한다.
- 원본에 없는 후기·수치·사진을 만들지 않는다. 회색 자리 표시가 남은 채로 납품하지 않는다.
- 이모지, 그라디언트, 네이비·체크 블루·후기 주황 외의 색을 쓰지 않는다.
