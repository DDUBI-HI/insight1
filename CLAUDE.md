# insight1 — 인싸이트러닝 AI 사무실

이 저장소는 여러 업무 도구를 한곳에 모은 공유 작업 공간이다. 각 도구의 상세 규칙은 해당 스킬의 `SKILL.md`가 정본이다.

| 스킬 | 트리거 | 정의 |
|------|--------|------|
| `/cardnews` | `"카드뉴스 만들어줘"` | `.claude/skills/cardnews/SKILL.md` |
| `/generic-redesign` | `"범용으로 바꿔"`, `"범용 과정으로 만들어"`, `"고객사 이름 빼고 리디자인"` | `.claude/skills/generic-redesign/SKILL.md` — 고객사 제안서 → 범용 과정 PPTX |
| `/slide` · `/slide-plan` | `"슬라이드 만들어"`, `"기획부터"` | `.claude/skills/slide/SKILL.md`, `.claude/skills/slide-plan/SKILL.md` |
| `/video-slide` | `"영상 강의 PPT"`, `"강의 영상 배경"`, `"촬영용 슬라이드"`, `"내용 넣었으니 PPT로"` | `.claude/skills/video-slide/SKILL.md` — 강의 내용 → 강사 합성용 배경 PPTX |

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

### 영상 강의 배경 덱 (video-slide)

영상 강의 촬영용 덱은 활성 테마 대신 자체 디자인 시스템(`.claude/skills/video-slide/references/design-system.md`)을 쓴다. 아래는 이 덱에만 적용되는 추가 규칙이다.

- **오른쪽 30%(x ≥ 896)는 강사 영상 합성 자리** — 배경만 두고 글자·도형·일러스트를 넣지 않는다.
- **하단 자막 영역(y ≥ 644)은 비운다** — GM은 그 위의 네이비 필(y 566–606)로 올리고 프로젝트의 `.gm-band`로 verify_deck에 알린다.
- **깔끔하되 심심하지 않게** — 텍스트 위주 장에는 라이브러리의 플랫 벡터 일러스트(편집 가능한 도형)를 1개 넣는다.
- **올드한 이미지는 교체** — 참고 자료의 오래된 클립아트·흑백 스톡 사진 등은 같은 의미의 일러스트로 바꾸고 보고한다 (판정 기준: design-system §7).
- 팔레트는 민트·초록·틸·네이비(템플릿 기준)이므로 단일 액센트 규칙의 예외다. `.theme-color-allow`는 빌더가 쓴다.
- SVG는 `build_deck.py`가 스펙(YAML)에서 순서대로 생성한다. 후처리 3단계 개별 호출과 `-s final`은 그대로 지킨다.
- 색 테마 `theme: mint|indigo|coral|violet`("같은 디자인에 색만 다르게"), 저시력 모드 `accessible: true`(본문 ≥ 20px — 장애 인식개선 덱·"글자 크게" 요청).
- **"내용은 바꾸지 말고 디자인만"** 요청은 `lock_content: true` — 슬라이드별 텍스트를 글자 단위로 보존(오탈자 포함, 보고만), GM·라벨 등 새 텍스트 추가 금지, 원본과 글자 대조(추가·누락 0) 후 납품. verify_deck은 `.gm-exempt`로 GM 검사를 건너뛰고 WARN을 남긴다.

### 출처

슬라이드 엔진은 slide-svg (MIT, Byungjun Jang) · ppt-master (MIT) · diagram-design (MIT)에서 가져왔다. 고지문: `.claude/skills/LICENSES/`.
