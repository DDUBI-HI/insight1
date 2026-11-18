# 교육 프로그램 상세페이지

홈페이지용 프로그램 상세 이미지를 `page.json` 하나로 만든다. 690px 폭으로 디자인하고 2배(1380px 폭) PNG 로 캡처한다.
제안서에서 만드는 절차는 `/program-page` 스킬(`.claude/skills/program-page/SKILL.md`)에 있다.

```bash
node program-page/scripts/build.mjs <page.json>            # 렌더 → <name>.png + index.html (page.json 옆)
node program-page/scripts/build.mjs <page.json> --check    # 구조만 검사
node program-page/scripts/build.mjs <page.json> --scale 1  # 690px 폭 PNG
node program-page/scripts/build.mjs <page.json> --strict   # 경고도 실패 처리
```

Playwright 가 필요하다. 클라우드 세션에는 설치돼 있고, 로컬에서는 `cd program-page && npm install`.

## 파일
| 경로 | 내용 |
|---|---|
| `page.css` | 디자인 시스템 (색·간격·블록). 원본 이미지와 1px 이내로 맞춤 |
| `scripts/build.mjs` | 검사 → HTML → PNG, 렌더 뒤 줄 꺾임·폭 넘침·이미지 누락 경고 |
| `examples/*.json` | 유형별 예시 5종 (참고자료 이미지는 비어 있어 회색 자리 표시로 렌더됨) |

## page.json

```jsonc
{
  "name": "Claude기반_AI_Agent_실무교육",   // PNG 파일명
  "type": "ai-practice",                    // 메모용: job-skill | ai-practice | teambuilding | leadership | solution
  "category": "AI PROGRAM",                 // 영문 대문자
  "title": "Claude 기반 AI Agent 실무 교육", // \n 으로 직접 줄바꿈 가능
  "info": [                                  // 알약 1–3칸, 칸 폭은 자동으로 같아짐
    { "icon": "user",  "label": "추천 대상", "value": "전 사원" },
    { "icon": "clock", "label": "교육 시간", "value": "8시간 (이론+실습+점검)" }
  ],
  "sections": [ /* 아래 5종 */ ]
}
```

`icon` 은 `assets/icons/tabler-outline/` 의 파일 이름 (`user`, `users`, `clock`, `check`, `target`, `calendar`, `school` …).

| type | 모양 | 항목 |
|---|---|---|
| `checks` | 네이비 체크 목록 | `items: ["문장", …]` |
| `bullets` | 회색 상자 + 점 목록 | `items: ["실습 이름", …]` |
| `modules` | 회색 상자 + 제목/설명 행, 사이 구분선 | `items: [{ "title", "desc", "code"? }]`, `numbering: "M" \| "01" \| "1"` (생략 시 번호 없음) |
| `quotes` | 후기 인용 + 사진 + 캡션 | `items: [{ "quote", "image", "caption" }]`, `columns` (기본 항목 수, 최대 4). `**강조**` 는 주황 |
| `images` | 이미지 격자 | `items: [{ "image", "caption"?, "sample"?, "fit"? }]`, `columns` (기본 3), `ratio` (기본 `"3 / 4"`). `sample: true` 면 SAMPLE 도장, `fit: "cover"` 면 꽉 채워 자름 |

모든 섹션은 `en`(영문 라벨)과 `title`(한글 제목)을 가진다. 이미지 경로는 `page.json` 기준 상대 경로.
