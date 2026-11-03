# 카드뉴스

Figma "카드뉴스" 페이지(Frame 1–7)를 HTML/CSS 로 옮긴 카드뉴스 디자인 시스템입니다.
**HTML 로 카드를 만들고 → Unsplash 사진을 받아 넣고 → 브라우저로 캡처해 PNG** 를 만듭니다.

```
cardnews/
├─ cardnews.css            디자인 시스템 (토큰 + 템플릿 13종)
├─ templates.html          템플릿 13종 견본 (자리 문구)
├─ COPY_GUIDE.md           문구·구성·사진 기준 (에이전트와 사람 공용)
├─ scripts/
│  ├─ build-deck.mjs       deck.json → index.html + images.json (검증 포함)
│  ├─ fetch-images.mjs     images.json → Unsplash 사진 다운로드, CREDITS.md 생성
│  └─ render.mjs           index.html → out/*.png (1080 × 1440) + out/overview.png
└─ decks/
   └─ 2026-11-corporate-training-trends/   예시: 현재 기업 교육의 트렌드
      ├─ deck.json         원본: 카드별 템플릿·문구·사진
      ├─ index.html        카드 13장 (생성됨)
      ├─ images.json       카드별 Unsplash 사진 ID·검색어 (생성됨)
      ├─ CREDITS.md        사진 출처 (자동 생성)
      └─ out/              결과 PNG (자동 생성)
```

## 템플릿

| 클래스 | Figma | 용도 |
|---|---|---|
| `cn-cover` | Frame 1 | 표지. 풀블리드 사진 + 하단 그라디언트, 알약 라벨·2줄 제목·소제목 |
| `cn-intro` | Frame 2 | 도입. 풀블리드 사진 + 상단 그라디언트, 가운데 소제목·제목·포인트 문구 |
| `cn-feature` | Frame 3 | 포인트. 상단 이미지, 2줄 제목(둘째 줄 `cn-hl` 포인트색), 설명 |
| `cn-story` | Frame 4 | 본문. 포인트색 라벨 + 제목, 이미지, 긴 설명 |
| `cn-checklist` | Frame 5 | 리스트. 제목 + 체크 항목 3개 |
| `cn-faq` | Frame 6 | FAQ. 질문 말풍선(회색) · 이미지 · 답변 말풍선(포인트색) |
| `cn-closing` | Frame 7 | 마무리 CTA. 사진 + 40% 블랙, 가운데 문구 |
| `cn-compare` | 확장 | 이전 → 지금 비교표 (회색 칸 → 포인트 블루 칸, 2–4행) |
| `cn-summary` | 확장 | 번호 목록 한 장 요약 (파란 번호 원 + 제목 + 한 줄 설명, 3–5행) |
| `cn-split` | 확장 | 위 사진(풀폭) + 아래 제목·체크 목록 |
| `cn-grid` | 확장 | 2 × 2 타일, `.is-point` 타일은 포인트 블루 |
| `cn-steps` | 확장 | 세로 단계 타임라인 (3–4단계, `.is-point` 로 단계 강조) |
| `cn-statement` | 확장 | 포인트 블루 전면 + 핵심 메시지 (하늘색 형광펜 강조) |

확장 템플릿은 공통 머리글 `.cn-head`(`.cn-kicker` 라벨 + 2줄 `.cn-title` + `.cn-sub`)를 씁니다.
보조 설명은 `#666`, 구분선은 `#dfdfdf`, 타일은 말풍선과 같은 `#ededed` 로 Figma 팔레트를 벗어나지 않습니다.

### 덱 구성 예 (샘플 13장)

표지 → 도입 → 비교(무엇이 바뀌었나) → 요약(한눈에 보기) → 트렌드별 카드 5장(포인트 · 본문 · 사진+체크 · 타일 · 단계)
→ 셀프 점검 → FAQ → 핵심 메시지 → 마무리.
같은 템플릿을 연달아 쓰지 말고, 사진 카드와 흰 카드, 구조 카드를 번갈아 배치하면 넘길 때 리듬이 생깁니다.

치수는 모두 Figma 1x(300 × 400) 그대로이며, 캡처할 때 3.6배로 키워 1080 × 1440 이 됩니다.
색·글자 크기는 `cardnews.css` 맨 위 `--cn-*` 변수와 루트 `tokens.json` 의 **Card news** 항목에 있습니다.

## 에이전트로 만들기 (`/cardnews`)

Claude Code 에서 주제만 입력하면 됩니다.

```
/cardnews 신입사원 온보딩 트렌드
/cardnews 팀장 리더십 교육 10 중간관리자
```

에이전트(`.claude/skills/cardnews/SKILL.md`)는 다음 순서로 진행합니다.
1. 구성과 문구를 쓰고, **카드별 초안 표를 보여주며 확인을 받습니다.**
2. 확인을 받으면 Unsplash 무료 사진을 고릅니다.
3. `deck.json` → `index.html` 을 만들고, push 해서 Actions 로 PNG 를 렌더합니다.
4. 결과 이미지를 직접 보고 검수한 뒤 전달합니다.

문구 기준은 [`COPY_GUIDE.md`](COPY_GUIDE.md) 에 있습니다.

### deck.json → index.html

덱의 원본은 `decks/<slug>/deck.json` 입니다. 카드마다 템플릿 이름과 문구 필드만 적습니다.
`index.html` 과 `images.json` 은 생성기가 만듭니다.

```bash
cd cardnews
npm run new -- decks/<slug> --check   # 검증만: 템플릿 필드, 행 개수, 줄 길이(실측 폭), 덱 구성 규칙
npm run new -- decks/<slug>           # index.html · images.json 생성
ALLOW_MISSING_IMAGES=1 STRICT=1 npm run render -- decks/<slug>   # 사진 없이 레이아웃만 검사
```

`STRICT=1` 렌더는 두 경우에 실패합니다. 글이 카드 밖으로 넘친 경우, 그리고 직접 나눈 줄보다 더 꺾인 경우입니다.

## 손으로 새 카드뉴스 만들기

1. `decks/2026-11-corporate-training-trends` 폴더에서 `deck.json` 만 새 폴더로 복사합니다 (예: `decks/2026-12-leadership/deck.json`).
2. `deck.json` 의 문구를 고치고 `npm run new -- decks/<slug>` 로 `index.html` 을 만듭니다.
   카드 순서·개수는 자유지만 표지로 시작해 `cn-closing` 으로 끝냅니다.
   PNG 파일 이름은 `<번호>-<name>` 이 됩니다.
3. 각 카드의 `photo` 에 내용에 맞는 사진을 지정합니다. 생성기가 이 내용으로 `images.json` 을 만듭니다.
   - `unsplash`: Unsplash 사진 페이지 주소 끝의 ID (`unsplash.com/photos/...-RdEFWm0N84o` → `RdEFWm0N84o`)
   - `query`: 영문 검색어. `unsplash` 를 비워 두면 검색 결과 중 첫 무료 사진을 자동으로 고르고 ID 를 기록합니다.
   - `alt`: 사진 설명 (한국어, 필수)
   - `file`: 저장할 파일 이름 (기본 `<name>.jpg`)
   - `position`: 사진 위치 조정, 예 `"30% 50%"`. 풀블리드 가로 사진은 가로 값만 효과가 있습니다.
4. 브랜치에 push 하면 GitHub Actions(`카드뉴스 렌더`)가 사진을 받고 PNG 를 렌더해 `out/` 에 커밋합니다.
   Actions 탭의 `cardnews-png` 아티팩트로도 받을 수 있습니다.

### 내 컴퓨터에서 직접 렌더

```bash
cd cardnews
npm ci
npx playwright install chromium
UNSPLASH_ACCESS_KEY=... npm run build   # = fetch(사진 받기) + render(PNG 캡처)
```

- 덱 하나만: `node scripts/fetch-images.mjs decks/<덱>` → `node scripts/render.mjs decks/<덱>`
- 사진 다시 받기: `node scripts/fetch-images.mjs decks/<덱> --force`
- 사진 없이 레이아웃만 확인: `ALLOW_MISSING_IMAGES=1 npm run render`
- 미리보기: `decks/<덱>/index.html` 을 브라우저로 열면 카드가 1.4배로 보입니다.

`render.mjs` 는 Pretendard 폰트가 안 읽히거나, 사진이 비어 있거나, 글이 카드 밖으로 넘치면 알려줍니다.

### Unsplash API 키 (필수, 무료)

사진은 공식 [Unsplash API](https://unsplash.com/developers)로 받습니다. 처음 한 번만 설정하면 됩니다.

1. https://unsplash.com/oauth/applications 에서 **New Application**을 만들고 **Access Key**를 복사합니다 (Demo 등급: 시간당 50회, 카드뉴스 용도로 충분).
2. GitHub 저장소 **Settings → Secrets and variables → Actions → New repository secret**에 이름 `UNSPLASH_ACCESS_KEY`로 등록합니다.
3. Actions 탭에서 **카드뉴스 렌더 → Run workflow**를 누르거나 브랜치에 다시 push 합니다.

로컬에서는 `UNSPLASH_ACCESS_KEY=... npm run build` 로 실행합니다. 키가 없으면 워크플로는 사진 받기와 렌더를 건너뛰고 안내만 남깁니다.

## 사진 라이선스

모든 사진은 [Unsplash License](https://unsplash.com/license)(상업적 사용 가능, 출처 표기 의무 없음)를 따릅니다.
Unsplash+ (유료) 사진은 쓰지 않습니다. 출처는 덱마다 `CREDITS.md` 에 자동으로 정리됩니다.

폰트: Pretendard (SIL Open Font License 1.1) — `fonts/LICENSE-Pretendard.txt`
