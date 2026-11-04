---
name: cardnews
description: 인싸이트러닝 카드뉴스를 주제만으로 만든다. 구성·문구·인스타그램 본문 작성 → 사용자 확인 → Unsplash 사진 선정 → HTML 생성 → GitHub Actions 렌더(1080×1440 PNG) → 시각 검수 → 이미지와 인스타 문구 전달. "/cardnews <주제>", "카드뉴스 만들어줘" 같은 요청에 사용.
argument-hint: <주제> [장수] [대상]
---

# /cardnews — 카드뉴스 에이전트

주제 하나로 `cardnews/` 디자인 시스템에 맞는 카드뉴스 덱을 만듭니다. 템플릿은 13종이고, 결과는 1080 × 1440 PNG입니다.
**문구를 쓰고 사용자에게 확인받기 전에는 렌더하지 않습니다.**

## 먼저 읽을 것
- `cardnews/COPY_GUIDE.md`: 문체, 덱 구성, 템플릿 선택, `deck.json` 필드, 줄 길이, 사진 기준. **반드시 읽고 시작합니다.**
- 참고 예시: `cardnews/decks/2026-11-corporate-training-trends/deck.json` (13장 완성본)
- 템플릿 모양: `cardnews/templates.html`, 출력 예시: 같은 덱의 `out/overview.png`

## 입력
`$ARGUMENTS` 에서 다음을 읽습니다.
- **주제** (필수)
- **장수** (기본 13, 7–20)
- **대상** (기본 "기업 HR·교육 담당자")

사용자가 문구나 자료를 함께 줬으면 그 문구를 우선합니다. 고칠 때는 길이를 맞추는 정도만 고칩니다.

## 절차

### 1. 조사 (필요할 때만)
- 주제에 사실 확인이 필요하면 WebSearch로 확인합니다. 예: 프레임워크 이름, 제도 변화.
- 확인한 내용만 쓰고, 출처는 `deck.json` 의 `sources` 에 적습니다. **확인되지 않은 수치·통계·인용은 쓰지 않습니다.**

### 2. 구성과 문구 초안
1. slug 를 정합니다: `YYYY-MM-<영문-주제>` (예 `2026-12-onboarding-trends`).
2. `cardnews/decks/<slug>/deck.json` 을 작성합니다.
   - COPY_GUIDE의 덱 구성표와 템플릿 선택표를 따릅니다.
   - 사진 칸에는 일단 `query`(영문)와 `alt` 만 넣습니다.
   - 인스타그램 게시물 문구를 `caption` 에 함께 씁니다(COPY_GUIDE §7: 첫 줄 후킹, 요약, 참여 유도, CTA, 해시태그 8–15개).
3. 검증합니다: `cd cardnews && node scripts/build-deck.mjs decks/<slug> --check`
   - 오류가 나면 문구를 고쳐 통과할 때까지 반복합니다. 메시지에 "약 N자 줄이세요"처럼 줄일 양이 나옵니다.
4. **사용자에게 초안 표를 보여주고 멈춥니다.** 표는 카드 번호 | 템플릿 | 문구 요약(제목과 핵심 문장) 형식입니다.
   - 표 아래에 인스타그램 문구 초안을 코드 블록으로 함께 보여줍니다. 문의 방법이 정해져 있지 않으면 확인을 요청합니다.
   - "이대로 진행할까요, 고칠 곳이 있나요?"라고 묻습니다.
   - 수정 요청이 오면 반영하고 3번(검증)부터 다시 합니다.

### 3. 사진 선정 (승인 후)
- 사진 칸마다 Unsplash 무료 사진을 찾습니다.
  - WebSearch 에 `allowed_domains: ["unsplash.com"]` 를 걸고, 쿼리에 `"Free Photo"` 를 넣습니다.
  - 결과 제목이 "Free Photo on Unsplash"인 개별 사진 페이지만 씁니다. "Unsplash+"는 쓰지 않습니다.
  - URL 끝의 ID 를 `photo.unsplash` 에, 페이지 URL 을 `photo.page` 에 넣습니다.
  - ID 가 `-` 로 시작하면 URL에 `--` 가 들어 있으니 주의합니다.
- 찾지 못하면 `unsplash` 를 비우고 `query` 만 둡니다. 렌더 단계에서 Unsplash API 검색 1순위 무료 사진이 자동으로 들어갑니다.
- COPY_GUIDE §6을 따릅니다: 글자 자리가 비어 있는 사진이어야 하고, 한 덱 안에서 구도가 반복되지 않아야 합니다.

### 4. 생성과 로컬 레이아웃 검사
```bash
cd cardnews
node scripts/build-deck.mjs decks/<slug>
ALLOW_MISSING_IMAGES=1 STRICT=1 node scripts/render.mjs decks/<slug>
```
- STRICT 실패(넘침, 줄 꺾임)가 나면 `deck.json` 을 고치고 다시 실행합니다.
- 이 로컬 렌더는 사진 없이 레이아웃만 보는 것입니다.
  - 생성된 `out/` 은 **커밋하지 않습니다**: 기존 덱이면 `git checkout -- decks/<slug>/out`, 새 덱이면 `rm -rf decks/<slug>/out`.
  - `images/` 는 gitignore 대상입니다.
- 로컬에 Playwright 가 없으면 `NODE_PATH` 에 전역 설치 경로를 지정하거나, 이 단계를 건너뛰고 CI 렌더에 맡깁니다.

### 5. 렌더 (GitHub Actions)
- 커밋할 파일은 `decks/<slug>/deck.json`, `index.html`, `images.json`, `caption.txt` 입니다. 커밋한 뒤 작업 브랜치에 push 합니다.
- push 하면 `.github/workflows/cardnews-render.yml` 이 다음을 처리합니다.
  - Unsplash API(`UNSPLASH_ACCESS_KEY` Secret)로 사진을 받습니다.
  - PNG 를 렌더합니다.
  - `out/*.png`, `CREDITS.md`, 사진가 정보가 채워진 `images.json` 을 `cardnews: render PNG [skip ci]` 커밋으로 올립니다.
- 그 커밋을 기다립니다. `git ls-remote` 로 브랜치 HEAD 가 바뀌는지 백그라운드에서 확인하면 됩니다. 이어서 pull 합니다.
- 워크플로가 실패하면 로그를 확인합니다.
  - 사진 ID 오류(404)면 다른 사진으로 바꿉니다.
  - "시간당 요청 한도를 다 썼습니다"면 코드 문제가 아닙니다. Unsplash 데모 키는 1시간에 50회까지이고, 사진 1장에 2회를 씁니다. 1시간 뒤 Actions에서 **카드뉴스 렌더 → Run workflow**를 실행하고 `deck` 에 덱 폴더 이름을 넣어 그 덱만 다시 렌더합니다 (`send_later` 로 예약해도 됩니다).
- 워크플로는 push 에서 바뀐 덱만 렌더합니다. 받은 사진은 Actions 캐시에 남아 다음 실행에서 다시 쓰입니다.

### 6. 시각 검수 (반드시 PNG 를 직접 봅니다)
- `out/overview.png` 와 사진 카드 PNG 를 하나씩 열어 확인합니다.
  - 글자가 얼굴이나 주요 피사체를 가리지 않는가
  - 사진이 카드 내용과 맞는가
  - 사진 위 글자가 충분히 읽히는가
  - 사진가나 구도가 연달아 반복되지 않는가
- 문제가 있으면 고칩니다.
  - 사진 교체 (ID 변경)
  - 다른 사진 카드와 사진 맞바꾸기
  - 인라인 이미지면 `position` 조정
  - 고친 뒤 4–5단계를 다시 합니다. **최대 2회** 반복하고, 그래도 남는 문제는 사용자에게 알립니다.
- `build-deck.mjs` 는 이미 받은 사진의 사진가 정보를 같은 ID 일 때 유지합니다. ID 를 바꾸면 다시 받습니다.

### 7. 전달
- `out/overview.png` 와 카드 PNG 를 사용자에게 보냅니다. 업로드 순서대로 01→13 파일 이름 순입니다.
- **인스타그램 문구**(`decks/<slug>/caption.txt`)를 복사해 바로 붙여넣을 수 있게 코드 블록으로 함께 보냅니다.
- 함께 알릴 것:
  - 덱 구성 요약
  - 사진 출처 `CREDITS.md`
  - PR 링크 (작업 브랜치에 열린 PR이 없으면 draft PR 을 만듭니다)

## 하지 말 것
- 사용자 확인 없이 2단계를 지나 렌더하지 않습니다.
- Unsplash 를 공식 API 가 아닌 방식(페이지 스크래핑, 브라우저 자동화, User-Agent 위장)으로 받지 않습니다. 봇 차단을 우회하지 않습니다.
- `index.html` 이나 `images.json` 을 손으로 고치지 않습니다. 항상 `deck.json` 을 고치고 `build-deck.mjs` 로 다시 만듭니다.
- `out/*.png` 를 손으로 만들거나 고치지 않습니다. PNG 는 CI 렌더 결과만 씁니다.
- `cardnews/cardnews.css` 를 덱 하나를 위해 고치지 않습니다. 새 레이아웃이 필요하면 사용자에게 제안합니다.
- 브랜드 규칙을 어기지 않습니다: 이모지, 근거 없는 수치, "여러분" 호칭.
