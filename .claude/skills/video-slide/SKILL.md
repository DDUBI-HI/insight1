---
name: video-slide
description: >
  영상 강의(이러닝) 촬영용 배경 PPT를 만든다. 사용자가 강의 내용(텍스트·개요·대본·PDF/PPT/DOCX)을 주면
  그대로 덱 스펙(YAML)으로 옮겨 민트·네이비 "영상 강의" 디자인 시스템으로 네이티브 PPTX를 바로 만든다.
  오른쪽 30%(x ≥ 896)는 강사 영상 합성을 위해 비워 두고, 하단 자막 영역도 비운다. 카드·표·차트·흐름 등
  25개 레이아웃과 편집 가능한 플랫 벡터 일러스트 35종, 색 테마 4종·저시력 모드을 쓰며, 참고 자료의 올드한 사진·클립아트는
  일러스트로 교체한다. "영상 강의 PPT", "강의 영상 배경", "촬영용 슬라이드", "이러닝 슬라이드",
  "강사 합성용 PPT", "내용 넣었으니 PPT로" 같은 요청이나 /video-slide 호출에 사용.
---

# /video-slide — 영상 강의 배경 덱

> 상위 규칙: 루트 `CLAUDE.md` (1280×720, 이모지 금지, 네이티브 SVG→PPTX, 후처리 3단계 개별 호출, GM 한 줄).
> 이 스킬은 그 위에서 **영상 강의 전용 디자인 시스템**(`references/design-system.md`)을 쓴다 — 활성 테마
> (`theme-active.json`)를 바꾸지 않고 자체 토큰(`scripts/vkit/tokens.py`)으로 그린다.

## 핵심 규칙 (요약 — 정본은 `references/design-system.md`)

1. **강사 영역**: 오른쪽 30% (x ≥ 896)에는 배경(민트)만. 글자·도형·일러스트 금지.
2. **자막 영역**: 하단 y ≥ 644 는 네이비 밴드만 (왼쪽 끝 작은 브랜드 표기 외 금지). 자막이 그 위에 얹힌다.
3. **콘텐츠 카드**: 흰 카드(x 28–880) 안, 안전 영역 x 64–844 에서만 그린다. 한 장 = 한 메시지.
4. **GM 필**: 콘텐츠 장마다 하단 네이비 필(✓ + 한 줄 so-what). 자막 영역 위(y 566–606)에 둔다 (`.gm-band`).
5. **일러스트**: 깔끔하되 심심하지 않게 — 텍스트 위주 장에는 라이브러리 일러스트 1개(카드형은 카드당 1개).
   팔레트 색만, 플랫, 얼굴 없는 인물. 이미지 클립아트·스톡 사진 대신 쓴다.
6. **올드 이미지 교체**: 참고 파일의 사진·일러스트가 올드하면(§7 체크리스트) 같은 의미의 라이브러리 일러스트로
   바꾸고, 바꾼 목록을 보고한다. 내용상 꼭 필요한 실제 화면·사진만 `image` 레이아웃으로 유지.
7. **영상 가독성**: 본문 17px 이상(최소 15px), 제목 38px, 문장은 짧게 — 자세한 설명은 `notes`(대본)로.

## 모드

| 모드 | 언제 | 차이 |
|---|---|---|
| **신규 제작** (기본) | 내용(텍스트·개요·대본)을 주고 "PPT로 만들어줘" | 문장을 슬라이드용으로 다듬고, GM 한 줄·섹션 라벨을 붙인다 |
| **내용 고정 리디자인** (`lock_content: true`) | 기존 덱(PDF/PPT)을 주며 "내용은 절대 바꾸지 말고 디자인만" | 아래 §내용 고정 규칙 |

### 색 테마 · 저시력 모드

- `theme:` — `mint`(기본, 템플릿 색) · `indigo`(인디고 + 라즈베리) · `coral`(딥틸 + 코랄) · `violet`(플럼 + 바이올렛).
  디자인(레이아웃·일러스트·영역)은 그대로, 색만 일관되게 바뀐다. "같은 디자인에 색만 다르게" 요청에 쓴다.
  프리셋 정의: `scripts/vkit/tokens.py` THEMES (새 테마는 7개 토큰 hex만 지정).
- `accessible: true` — 저시력(시각장애) 고려: 본문 최소 20px(`min_fs`로 조정), 제목 42px, 굵기 ≥ 500,
  회색 글자 진하게, 줄간격 ≥ 1.38. 장애 인식개선·접근성 교육 덱이나 "글자 크게" 요청에 켠다.
  예외(조밀한 법령 연표·차트 수치 등)는 보고에 적는다.

### 내용 고정 규칙 (lock_content)

- 슬라이드별 텍스트는 원본과 **글자 단위로 동일** — 오탈자·띄어쓰기·문장부호까지 그대로 둔다(고치지 않고 보고만).
  바뀌어도 되는 것은 줄바꿈 위치와 글자 크기·색·배치뿐. 장 수·순서도 원본 그대로(퀴즈 문제/정답 장 포함).
- 새 텍스트를 넣지 않는다: GM 필, 「 」 섹션 라벨, PART 라벨, 자동 번호 배지, 브랜드 표기 모두 꺼진다(빌더가 자동 처리).
  GM이 없으므로 빌더가 `.gm-exempt`를 쓰고 verify_deck은 GM 검사를 건너뛰며 WARN으로 사유를 남긴다.
- 원본의 불릿 기호(•, ◆)는 도형 마커로 바꾼다. 한 문장이 여러 줄로 끊긴 것은 불릿으로 쪼개지 말고 문단으로 둔다.
- 이미지 속 글자(표 캡처, 도식, 스탬프 등)는 고해상도로 렌더해 **그대로 전사**하고 편집 가능한 텍스트로 다시 만든다.
  실제 화면 캡처처럼 내용 자체인 이미지는 이미지로 유지한다. 올드한 장식 이미지는 일러스트로 교체(§7).
- **글자 대조 검증 필수**: 원본 텍스트 레이어 + 전사본과, 빌드된 SVG·내보낸 PPTX의 슬라이드별 글자 집합을 비교해
  추가·누락 0을 확인한다 (`build()`가 `page_texts.json`을 남긴다 — 예시 스크립트 구조는 아래 §덱 스크립트).

### 덱 스크립트 (장마다 구성이 다른 기존 덱)

YAML 대신 `output/<project>/build.py`에서 `build_deck.build(spec, project, spec_dir, extra)`를 호출한다.
`extra`에 덱 전용 레이아웃 `{"name": (fn, needs_gm, role)}`를 넣고, 스크립트 끝에서 원본 대조를 실행한다.
덱 전용 레이아웃이라도 셸·토큰·일러스트·`prim`만 쓰고 영역 규칙을 지킨다(zone_check가 같이 돈다).
범용으로 쓸 만한 레이아웃은 `layouts.py`로 올린다.

## 입력

- 강의 내용: 붙여넣은 텍스트 / 개요 / 강의 대본 / 파일(PDF·PPTX·DOCX). 형식은 자유 — 스펙 변환은 Claude가 한다.
- 과정명(헤더 라벨), 파일명: 없으면 내용에서 정한다. 묻지 않고 진행한다 ("넣으면 바로 PPT").
- 사용자가 직접 YAML을 써도 된다 — `examples/sample_deck.yaml`이 전 레이아웃 예시, 필드는 `references/layouts.md`.
- 파일이면 먼저 텍스트로 변환한다:
  `.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/source_to_md/pdf_to_md.py <file>`
  (PPTX는 `ppt_to_md.py`, DOCX는 `doc_to_md.py`). 원본의 이미지도 함께 보고 design-system §7로 교체 여부를 판단한다.

## 절차 (직렬, 확인 대기 없음)

### 0. 준비 (세션당 한 번)

```bash
pip install -r .claude/skills/slide/requirements.txt
```
클라우드 세션 렌더 확인용 폰트: Pretendard가 없으면 `fonts/PretendardVariable.woff2`를 TTF로 풀어 `~/.fonts`에
설치한다 (설치 안 해도 PPTX는 정상 — 렌더 미리보기만 대체 폰트가 된다).

### 1. 스펙 작성 — `output/<project>/deck.yaml`

- 내용을 장 단위로 나누고, 장마다 **내용의 모양**으로 레이아웃을 고른다 (`references/layouts.md` §선택표).
  같은 레이아웃을 3장 연속 쓰지 않는다. 표지 → (강의순서) → 섹션 → 본문… → (요약) → 엔딩.
- 제목은 `"초록 부분 | 네이비 부분"` 투톤, 20자 안팎. 붙여 쓰려면 `"개인정보|란?"`.
- `gm`: 콘텐츠 장마다 필수 — 제목 재진술이 아닌 편집적 한 줄(합니다체, 35자 이내).
- `illust`: 키 이름 지정 또는 `auto`(키워드로 자동 선택). 목록은 `references/design-system.md` §6.
- `notes`: 강사 대본/설명. 슬라이드에서 뺀 자세한 내용은 여기로 옮긴다.
- 사용자가 준 문구는 최대한 그대로 쓰되, 슬라이드 문장은 짧게 끊는다. 수치·법령은 지어내지 않는다.
- YAML 함정: `?` `,` `:` 가 든 문장은 `[a, b]` 흐름 표기 대신 블록 표기(`- q: …`)나 따옴표를 쓴다.

### 2. 빌드

```bash
.claude/skills/slide/scripts/_py.sh .claude/skills/video-slide/scripts/build_deck.py output/<project>/deck.yaml
```
- `[ERROR]`(영역 침범·GM 누락·이미지 없음)는 0이어야 한다. `[WARN]`(글자 넘침·축소)은 문장을 줄여 다시 빌드.
- 스펙의 `project:`가 출력 폴더 이름이다 (`output/<project>/`). 다시 빌드하면 SVG를 전부 새로 쓴다.

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
.claude/skills/slide/scripts/_py.sh .claude/skills/video-slide/scripts/finish.py <project> "<파일명>.pptx"
```
- verify_deck PASS가 아니면 납품하지 않는다.
- `output/<project>/_pptx_render/gridN.png`를 **전부 직접 본다**: 넘침·겹침·잘림·빈 공간, 그리고
  오른쪽 30%가 비었는지. 문제가 있으면 deck.yaml 수정 → 2–4단계 재실행.
- LibreOffice 렌더는 한글–숫자 사이에 공백을 더 넣어 보이게 한다("4 가지") — 파일 문제 아님.
- 납품: `output/_deliver/<파일명>.pptx` (또는 `--dst`, `$VIDEO_SLIDE_DST`). 클라우드 세션은 파일 전달로 넘긴다.

### 5. 보고

- 파일명·장수, 레이아웃 구성 한 줄, 교체한 올드 이미지 목록(원본 → 일러스트), 줄이거나 노트로 옮긴 문장,
  확인 필요 사항(지어내지 않은 수치의 출처 등).

## 파일

| 경로 | 내용 |
|---|---|
| `references/design-system.md` | 디자인 시스템 정본 — 영역, 색, 서체, 컴포넌트, 일러스트·이미지 규칙 |
| `references/layouts.md` | 레이아웃 24종 필드 레퍼런스 + 내용→레이아웃 선택표 |
| `examples/sample_deck.yaml` | 전 레이아웃 샘플 (개인정보보호 기본교육) |
| `scripts/build_deck.py` | 스펙 → SVG + notes, 영역 검사 · `build()` API (덱 스크립트용) · `page_texts.json` |
| `scripts/finish.py` | verify → zip → 렌더 → 납품 |
| `scripts/gallery.py` | 일러스트 전체 시트 → `output/_vs_gallery/` |
| `scripts/vkit/tokens.py` | 색·서체·영역 좌표 (SSOT) |
| `scripts/vkit/frame.py` · `layouts.py` · `illust.py` · `prim.py` | 셸 / 레이아웃 / 일러스트 / SVG 기본 요소 |

## 확장

- 레이아웃 추가: `layouts.py`에 `fn(p) -> svg` 작성 → `LAYOUTS`에 등록(GM 필요 여부·파일 역할) →
  필요하면 `SHELL_TITLE`에 추가 → `references/layouts.md`에 필드 기록 → 샘플에 1장 추가해 렌더 확인.
- 일러스트 추가: `illust.py`에 200×160 박스 드로잉 작성 → `LIB`에 (함수, 의미, 키워드) 등록 →
  `gallery.py`로 확인. 스타일 계약(§6)을 지킨다.
- 색 변경(예: 브랜드 네이비 `#012281`로): `tokens.py`만 바꾸면 전 레이아웃에 반영된다. 문서 표도 함께 고친다.
