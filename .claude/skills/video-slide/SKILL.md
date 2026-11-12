---
name: video-slide
description: >
  영상 강의(이러닝) 촬영용 배경 PPT를 만든다. 사용자가 강의 내용(텍스트·개요·대본·PDF/PPT/DOCX)을 주면
  그대로 덱 스펙(YAML)으로 옮겨 민트·네이비 "영상 강의" 디자인 시스템으로 네이티브 PPTX를 바로 만든다.
  오른쪽 30%(x ≥ 896)는 강사 영상 합성을 위해 비워 두고, 하단 자막 영역도 비운다. 카드·표·차트·흐름 등
  19개 레이아웃과 편집 가능한 플랫 벡터 일러스트 20종을 쓰며, 참고 자료의 올드한 사진·클립아트는
  일러스트로 교체한다. "영상 강의 PPT", "강의 영상 배경", "촬영용 슬라이드", "이러닝 슬라이드",
  "강사 합성용 PPT", "내용 넣었으니 PPT로" 같은 요청이나 /video-slide 호출에 사용.
---

# /video-slide — 영상 강의 배경 덱

> 상위 규칙: 루트 `CLAUDE.md` (1280×720, 이모지 금지, 네이티브 SVG→PPTX, 후처리 3단계 개별 호출, GM 한 줄).
> 이 스킬은 그 위에서 **영상 강의 전용 디자인 시스템**(`references/design-system.md`)을 쓴다 — 활성 테마
> (`theme-active.json`)를 바꾸지 않고 자체 토큰(`scripts/vkit/tokens.py`)으로 그린다.

## 핵심 규칙 (요약 — 정본은 `references/design-system.md`)

1. **강사 영역**: 오른쪽 30% (x ≥ 896)에는 배경(민트 + 네이비 무대 밴드)만. 글자·도형·일러스트 금지.
2. **자막 영역**: 하단 y ≥ 644 는 네이비 밴드만 (왼쪽 끝 작은 브랜드 표기 외 금지). 자막이 그 위에 얹힌다.
3. **콘텐츠 카드**: 흰 카드(x 28–880) 안, 안전 영역 x 64–844 에서만 그린다. 한 장 = 한 메시지.
4. **GM 필**: 콘텐츠 장마다 하단 네이비 필(✓ + 한 줄 so-what). 자막 영역 위(y 566–606)에 둔다 (`.gm-band`).
5. **일러스트**: 깔끔하되 심심하지 않게 — 텍스트 위주 장에는 라이브러리 일러스트 1개(카드형은 카드당 1개).
   팔레트 색만, 플랫, 얼굴 없는 인물. 이미지 클립아트·스톡 사진 대신 쓴다.
6. **올드 이미지 교체**: 참고 파일의 사진·일러스트가 올드하면(§7 체크리스트) 같은 의미의 라이브러리 일러스트로
   바꾸고, 바꾼 목록을 보고한다. 내용상 꼭 필요한 실제 화면·사진만 `image` 레이아웃으로 유지.
7. **영상 가독성**: 본문 17px 이상(최소 15px), 제목 38px, 문장은 짧게 — 자세한 설명은 `notes`(대본)로.

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
| `references/layouts.md` | 레이아웃 19종 필드 레퍼런스 + 내용→레이아웃 선택표 |
| `examples/sample_deck.yaml` | 전 레이아웃 샘플 (개인정보보호 기본교육) |
| `scripts/build_deck.py` | 스펙 → SVG + notes, 영역 검사 |
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
