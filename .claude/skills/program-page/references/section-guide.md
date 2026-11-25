# 섹션 가이드 — 교육 유형별 목차 구성

상세페이지는 **교육 유형에 따라 섹션 구성이 다르다.** 원본 제안서를 읽고 먼저 유형을 정한 뒤, 아래 레시피에서 출발한다.
레시피는 출발점이다. 원본에 내용이 없는 섹션은 지어내지 않고 빼며, 원본이 다른 구성을 강하게 요구하면 (예: 기획 의도가 핵심인 리더십 과정) 섹션을 더하거나 바꾼다.

예시 5종(`program-page/examples/`)이 각 레시피의 정답 사례다. 새 페이지를 만들 때 가장 가까운 예시를 복사해 시작한다.

---

## 1. 유형 판별

| 유형 (`type`) | 이런 원본이면 | 예시 |
|---|---|---|
| `job-skill` 직무 스킬 실습형 | 특정 업무 산출물(보고서·기획서·엑셀·PPT)을 만드는 실습이 중심. 대상이 직무로 설명됨 ("보고서 작성이 많은 실무자") | `01-report-writing.json` |
| `ai-practice` AI 실무 모듈형 | AI·디지털 도구를 단계별 모듈(M1…M7)로 익히는 과정. 이론→실습→점검 흐름 | `02-ai-agent.json` |
| `teambuilding` 팀빌딩·조직활성화 | 게임·미션·레이싱 등 활동 순서로 진행. 학습보다 경험·단합이 목적 | `03-survival-racing.json` |
| `leadership` 리더십·관리자 | 팀장·중간관리자 대상. 관점 전환·질문형 주제. "왜 이 교육인가"가 중요 | `04-ai-team-leader.json` |
| `solution` 솔루션·진단형 | 진단지·유형검사(DISC 등)·워크시트를 쓰는 역량 과정 (팔로워십, 커뮤니케이션, 협업) | `05-proactive-followership.json` |

둘 이상에 걸치면 **교육 내용이 어떻게 진행되는지**로 정한다: 활동 순서 → teambuilding, 도구 단계 → ai-practice, 산출물 실습 → job-skill, 진단·도구 → solution, 관점·질문 → leadership.

## 2. 유형별 레시피

| 유형 | category (예) | info 1칸째 | 섹션 순서 |
|---|---|---|---|
| job-skill | `JOB-SKILL PROGRAM` | `check` 교육 키워드 (예 "실습 중심 / 직무별 맞춤 사례") | ① `checks` RECOMMENDED FOR / 추천 대상 → ② `bullets` PROGRAM / 핵심 실습 |
| ai-practice | `AI PROGRAM` | `user` 추천 대상 | ① `checks` EDUCATION GOAL / 교육 목표 → ② `modules` PROGRAM / 교육 내용 (`numbering: "M"`) |
| teambuilding | `TEAMBUILDING` | `user` 추천 대상 | ① `checks` TEAMBUILDING GOAL / 프로그램 목표 → ② `modules` PROGRAM / 프로그램 구성 (`numbering: "01"`) → ③ `quotes` EXAMPLE / 참고자료 (후기가 있을 때) |
| leadership | `LEADERSHIP PROGRAM` · `AI LEADERSHIP` | `user` 추천 대상 | ① `checks` EDUCATION GOAL / 교육 목표 → ② `checks` PROGRAM PURPOSE / 기획 의도 (원본에 배경·필요성이 있을 때) → ③ `modules` PROGRAM / 교육 내용 (번호 없음) |
| solution | `SOLUTION PROGRAM` | `user` 추천 대상 | ① `checks` EDUCATION GOAL / 교육 목표 → ② `modules` PROGRAM / 교육 내용 (번호 없음) → ③ `images` EXAMPLE / 참고자료 (진단지·워크시트, `sample: true`) |

info 2칸째는 항상 `clock` 교육 시간이다.

그 밖의 category 예: `COMMUNICATION PROGRAM`, `ONBOARDING PROGRAM`, `DX PROGRAM`, `CS PROGRAM`, `HR PROGRAM`. 짧은 영문 대문자 한 줄.

### 언제 무엇을 고르나
- **추천 대상을 알약에 둘까, 섹션으로 뺄까**: 대상이 한 줄 명사구("전 사원", "팀장 / 중간관리자 / 조직 리더")면 알약. 대상이 직무·상황별로 여러 갈래(3–4줄)면 `checks` 섹션으로 빼고, 알약 1칸째는 `check` 교육 키워드로 바꾼다.
- **`bullets` vs `modules`**: 항목이 실습 이름뿐이면(설명 없음, 5–8개) `bullets`. 항목마다 제목 + 세부 내용이 있으면 `modules`.
- **번호**: 도구·단계형 모듈 5개 이상 → `"M"` (M1, M2…). 순서대로 진행되는 활동(팀빌딩 라운드) → `"01"` (01., 02.…). 주제 묶음(리더십·솔루션) → 번호 없음.
- **참고자료**: 원본에 실제 후기 문장 + 현장 사진이 있으면 `quotes`, 진단지·워크시트·교재 샘플 이미지가 있으면 `images`. 둘 다 없으면 섹션을 뺀다 (자리 표시 이미지로 납품 금지).
- **기획 의도**: 원본에 "배경", "필요성", "기획 방향"이 있고 목표와 다른 이야기(왜 지금 이 교육인가)를 할 때만 넣는다.

### 섹션 라벨 어휘 (영문 / 한글)
| en | title | 쓰는 곳 |
|---|---|---|
| RECOMMENDED FOR | 추천 대상 | job-skill |
| EDUCATION GOAL | 교육 목표 | ai-practice · leadership · solution |
| TEAMBUILDING GOAL | 프로그램 목표 | teambuilding |
| PROGRAM PURPOSE | 기획 의도 | leadership (필요 시 다른 유형도) |
| PROGRAM | 교육 내용 · 핵심 실습 · 프로그램 구성 | 모든 유형 |
| EXPECTED EFFECT | 기대 효과 | 원본이 기대효과를 강조할 때 (`checks`) |
| EXAMPLE | 참고자료 | quotes · images |

새 라벨이 필요하면 같은 형식(영문 대문자 2–3단어 / 한글 2–5자)으로 만든다.

## 3. 문구 규칙

### 공통
- 범용화: `.claude/skills/generic-redesign/references/generic-rules.md` 를 따른다. 고객사명·현장명·날짜·인원·예산·강사 이력은 상세페이지에 넣지 않는다.
- 이모지 금지. 근거 없는 수치 금지. 원본에 없는 내용은 지어내지 않는다.
- 목록 안 구분은 ` / ` 또는 ` · ` (가운데 점). 하위 주제 나열은 ` / ` 가 기본, 원본이 `|` 를 쓰면 유지해도 된다.

### 칸별
| 칸 | 형식 | 길이 (한 줄 기준) |
|---|---|---|
| `category` | 영문 대문자 | 3단어 이하 |
| `title` | 공식 과정명. 원본의 과정명을 범용으로 다듬음 | 18자 안팎 (한 줄). 넘으면 `\n` 으로 의미 단위로 끊어 2줄 |
| info `value` | 명사구. 시간은 "N시간" + 필요하면 괄호 구성 ("8시간 (이론+실습+점검)", "6시간 집중과정"). 범위는 "2~4시간 ※ 인원과 운영 환경에 따라 조정 가능" | 30자 이하 |
| `checks` 목표 | **"~한다 / ~할 수 있다"** 평서 다짐체. 핵심어를 ‘ ’ 로 감쌀 수 있음 | 3–4개, 각 36자 이하 |
| `checks` 추천 대상 | **"~한/~싶은 구성원·실무자"** 명사형 종결 | 3–4개, 각 36자 이하 |
| `checks` 기획 의도 | 목표와 같은 다짐체 | 3–4개 |
| `bullets` | 실습 이름 명사구 ("기획 보고서 작성") | 5–8개, 각 24자 이하 |
| `modules.title` | 모듈 이름 명사구 또는 질문 ("지능을 개발할 수 있는가?") | 24자 이하 |
| `modules.desc` | 세부 주제 2–4개를 ` / ` 로, 또는 한 문장 요약 | 38자 이하 (한 줄) |
| `quotes.quote` | 원본 후기 그대로, 핵심 구를 `**…**` 로 강조(주황). `\n` 으로 2–3줄 | 한 줄 13자 안팎 |
| `quotes.caption` / `images.caption` | 고객사는 이니셜 + "사" ("I사 조직활성화 과정") | 16자 이하 |

길이는 `build.mjs` 가 렌더 뒤 실제로 재서 꺾이면 경고한다. 경고가 나면 문구를 줄이고, 정말 두 줄이 필요하면 `\n` 으로 의미 단위로 끊는다 (체크 항목 두 줄은 페이지당 1개까지).

## 4. 원본 → 칸 매핑

| 원본에서 찾을 것 | 넣을 곳 |
|---|---|
| 과정명 · 프로그램명 | `title` |
| 교육 대상 · 참석자 | info 추천 대상 또는 `RECOMMENDED FOR` 섹션 |
| 교육 시간 · 일정(총 시간만) · 운영 방식 | info 교육 시간 |
| 교육 목적 · 목표 · 학습 목표 | `EDUCATION GOAL` / `TEAMBUILDING GOAL` |
| 배경 · 필요성 · 기획 방향 | `PROGRAM PURPOSE` (leadership 중심) |
| 커리큘럼 표 · 세부 일정표 · 모듈 | `PROGRAM` 섹션. 시간대별 행은 주제 단위로 3–7개 모듈로 묶는다. 시간·분량 칸은 버린다 |
| 실습 과제 목록 | `bullets` 핵심 실습 |
| 교육 후기 · 만족도 코멘트 + 현장 사진 | `quotes` |
| 진단지 · 워크시트 · 교재 페이지 | `images` (`sample: true`) |
| 특징 · 차별점 · 키워드 | info `교육 키워드` (job-skill) |
| 예산 · 강사 · 일정 날짜 · 고객사 정보 | 넣지 않음 |

원본 하나에 과정이 여러 개면 **과정마다 페이지 하나**를 만든다.
