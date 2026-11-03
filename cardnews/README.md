# 카드뉴스

Figma "카드뉴스" 페이지(Frame 1–7)를 HTML/CSS 로 옮긴 카드뉴스 디자인 시스템입니다.
**HTML 로 카드를 만들고 → Unsplash 사진을 받아 넣고 → 브라우저로 캡처해 PNG** 를 만듭니다.

```
cardnews/
├─ cardnews.css            디자인 시스템 (토큰 + 템플릿 7종)
├─ templates.html          템플릿 견본 (Figma 자리 문구 그대로)
├─ scripts/
│  ├─ fetch-images.mjs     images.json → Unsplash 사진 다운로드, CREDITS.md 생성
│  └─ render.mjs           index.html → out/*.png (1080 × 1440) + out/overview.png
└─ decks/
   └─ 2026-11-corporate-training-trends/   예시: 현재 기업 교육의 트렌드
      ├─ index.html        카드 7장
      ├─ images.json       카드별 Unsplash 사진 ID·검색어
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

치수는 모두 Figma 1x(300 × 400) 그대로이며, 캡처할 때 3.6배로 키워 1080 × 1440 이 됩니다.
색·글자 크기는 `cardnews.css` 맨 위 `--cn-*` 변수와 루트 `tokens.json` 의 **Card news** 항목에 있습니다.

## 새 카드뉴스 만들기

1. `decks/2026-11-corporate-training-trends` 폴더를 복사해 이름을 바꿉니다 (예: `decks/2026-12-leadership`).
2. `index.html` 에서 문구를 고칩니다. 카드 순서·개수는 자유지만 표지로 시작해 `cn-closing` 으로 끝냅니다.
   각 카드의 `data-name` 이 PNG 파일 이름이 됩니다.
3. `images.json` 에 카드마다 내용에 맞는 사진을 지정합니다.
   - `unsplash`: Unsplash 사진 페이지 주소 끝의 ID (`unsplash.com/photos/...-RdEFWm0N84o` → `RdEFWm0N84o`)
   - `query`: 검색어. `unsplash` 를 비워 두면 검색 1순위 사진을 자동으로 고르고 ID 를 기록합니다.
   - `file`: `index.html` 의 `<img src="images/...">` 와 같은 이름
   - 사진 위치를 옮기려면 `<img style="object-position: 50% 70%">` 처럼 지정합니다.
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
