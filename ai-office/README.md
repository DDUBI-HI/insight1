# 인싸이트러닝 AI 사무실 (ai-office)

AI 비서실장과 전문팀 3개가 3D 사무실에서 일하는 모습을 보여 주고, **n8n(Docker)** 이 맡긴 일을 **Windows 의 Claude Code(`claude -p`)** 로 처리하는 로컬 시스템입니다.
외부 의존성 없이 Node.js 20 이상만 있으면 돌아갑니다(`npm install` 불필요).

- 초보자용 설치·사용법: [`docs/사용설명서.md`](docs/사용설명서.md)
- 안전한 테스트 자료: [`test-data/README.md`](test-data/README.md)

## 구조

```
n8n (Docker, 새 워크플로만 추가)            업무 패널·3D 사무실 (브라우저)
  │  POST http://host.docker.internal:8765/api/jobs   │  http://127.0.0.1:8765
  │  Header X-Office-Token                            │
  ▼                                                   ▼
┌──────────── 로컬 브리지 bridge/server.mjs (Windows, 127.0.0.1) ────────────┐
│ Host 헤더 확인 · 토큰 인증 · 작업 허용 목록(bridge/jobs) · 한 번에 한 작업 │
│ 승인함(사람 확인) · 작업 기록 · 3D 스냅샷(/api/office)                      │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │ claude -p --output-format stream-json --settings <작업별 허용 도구>
               ▼   (프롬프트는 표준입력, 셸을 거치지 않음)
   C:\AI-OFFICE\agents\slide-svg          ← C:\JY\slide-svg 의 복사본 (/slide, /generic-redesign, automation/cafe_inquiry)
   C:\AI-OFFICE\agents\insight1-cardnews  ← GitHub DDUBI-HI/insight1 복사본 (/cardnews)
   결과 → C:\AI-OFFICE\office-data\...    (새 파일만, 덮어쓰지 않음)
```

## 직원과 작업

| 직원 | 작업 type | Claude 도구 |
|---|---|---|
| 비서실장 | `chief.request`, `chief.briefing` | 없음(판단만) / 사용 안 함 |
| 문의분석 | `inquiry.analyze` | 없음 — 카탈로그는 브리지가 프롬프트에 넣음 |
| 제안서작성 | `proposal.draft`(승인 후), `proposal.generic`, `inquiry.queue` | slide-svg 스크립트(`_py.sh`), `output/**` 쓰기, (`inquiry.queue` 만) `n8n-local` 표 읽기 |
| 프로필분석 | `instructor.intake` | 없음 — 글자 뽑기는 브리지가 slide-svg 변환기를 고정 인자로 실행 |
| 강사풀관리 | `instructor.deck_add`(폴더 감시로도 시작), `instructor.verify`, `instructor.redesign` | 없음 — PPT 편집은 `tools/instructor_deck.py`(python-pptx, 기존 장 복제) / 사용 안 함 / slide-svg 스크립트 |
| 트렌드리서치 | `trend.research` | WebSearch, WebFetch |
| 카드뉴스 | `cardnews.draft`, `cardnews.revise`, `cardnews.render`(승인 후) | 초안: `cardnews/decks/**` 쓰기·build-deck 검증 / 완성: git·node 추가 |

승인함 종류: 맞춤 초안 시작, 비서실장 제안 실행, 제안서 검토, 디자인 확인, 강사풀 반영, 카드뉴스 초안 승인·수정 요청, 인스타그램 게시(미연동 → 수동 게시 안내).

## 기존 자산 재사용

- **TEAM 1** 은 `slide-svg/automation/cafe_inquiry`(n8n 데이터 표 `제안서_작업대기` → `/slide` revision → n8n 웹훅 검토 메일)를 그대로 씁니다. `inquiry.queue` 는 `scheduled_task_prompt.md` 를 그대로 실행하고, `proposal.draft` 는 `jobs prepare`(범용 프로젝트 복제 + brief) 헬퍼를 호출한 뒤 같은 수정 규칙으로 Claude 를 돌립니다.
- 범용본 매칭은 `automation/cafe_inquiry/catalog.json`(범용본 10종) 을 씁니다.
- 3D 화면은 [claude-3d-frog-office](https://github.com/d-onworks/claude-3d-frog-office) (MIT, `web/LICENSE-claude-3d-frog-office`, 가져온 커밋 `e00f953`)의 화면 코드·그림을 그대로 쓰고, 문구 일부와 업무 패널 단추만 바꿨습니다(`[AI-OFFICE]` 주석). 원래의 Claude Code 훅 방식 대신, 브리지가 같은 `GET /api/office` 형식으로 AI 직원 상태를 내보냅니다.

## 개발

```bash
cd ai-office
npm test                 # 단위 + 통합(데모 모드) 시험
npm run demo             # http://127.0.0.1:8766 (가짜 Claude, 사용량 0)
```

- 데모 모드는 `bridge/mock-claude.mjs` 가 `claude -p` 의 stream-json 을 흉내 냅니다.
- 설정: `config.example.json` → `config.json`(git 제외). 토큰: `<dataDir>/secret/bridge-token.txt`(처음 실행 때 생성, git·설정 파일에 두지 않음).
- Windows 스크립트(`scripts/*.ps1`)는 Windows PowerShell 5.1 기준, UTF-8 BOM·CRLF 로 저장합니다.
