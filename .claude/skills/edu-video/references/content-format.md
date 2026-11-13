# 콘텐츠 입력 형식 (content YAML)

사용자가 원고(텍스트·워드·PDF·기존 PPT 등 어떤 형태든)를 주면 Claude가 이 YAML로 옮긴다. 사용자가 직접 써도 된다.
견본: `examples/privacy_basics.yaml` (17종 레이아웃을 모두 쓴 21장 덱).

## 덱 설정

```yaml
project: edu_video_privacy_1        # output/<project>/ (영문·숫자·_ 만)
deliver: 개인정보보호_1차시.pptx      # 납품 파일명
title: 개인정보보호 기본 교육          # 선택 (기본: 표지 제목)
stage: tint                          # tint(강사 영역 연한 네이비) | plain(흰색)
logo: true                           # 표지·엔딩 Insightlearning 로고
slides: [...]
```

## 공통 필드 (콘텐츠 화면)

| 필드 | 필수 | 설명 |
|---|---|---|
| `layout` | ✓ | 아래 17종 중 하나 |
| `label` | | 라벨 pill — 차시 번호·소단원 (`1-1. 개인정보 정의`) |
| `title` | ✓ | 제목 한 줄 (한글 약 17자) |
| `key` | ✓ | 핵심 한 줄 (GM, 한글 약 22자) — 제목을 반복하지 않는 so-what |
| `say` | 권장 | 강의 원고 → PPTX 발표자 노트. 화면 핵심 문구를 꼭 포함한다 (접근성 A7) |
| `illust` | | 일러스트 이름 (design-system.md §6) |
| `minutes` | | 노트에 적을 예상 시간 (기본 1) |

텍스트 안 `**굵게**`는 네이비 Bold 강조, ` | `는 강제 줄바꿈이다.

> **YAML 함정.** ① 쉼표가 든 문장을 `[a, b]` 목록에 넣으면 쉼표에서 쪼개진다. 블록 목록(`- 문장`)을 쓰거나 따옴표로 감싼다(빌더가 1글자 항목을 잡아낸다). ② `no:`는 YAML에서 false로 읽힌다. 챕터 번호는 자동으로 매기고, 바꿀 때만 `number:`를 쓴다. ③ `**`로 시작하는 문장은 따옴표로 감싼다.

## 레이아웃별 필드

```yaml
- layout: cover          # 네이비 표지
  eyebrow: 법정의무교육 · 1차시
  title: [개인정보보호, 기본 교육]     # 최대 2줄 × 약 11자
  sub: 정의와 유형, 안전한 처리 원칙
  meta: 강사 OOO
  illust: shield                     # 기본 graduate

- layout: chapter        # 번호 자동 (number: 로 지정 가능)
  title: 개인정보의 정의              # 2줄 × 약 9자
  sub: 무엇이 개인정보인지부터
  illust: id_card                    # 기본 book

- layout: agenda
  title: 오늘의 학습 순서
  items: [정의, 유형, 처리 원칙, 사례, 퀴즈와 정리]   # 2–6개, 각 한 줄
  current: 2                         # 선택 — 진행 위치 강조
  key: …

- layout: concept        # 정의 문장 + 강조 구 + 일러스트
  lines: [사망자의 정보라도, 유족과의 관계를 알 수 있는 정보는]
  emphasis: 유족의 개인정보에 해당
  illust: question

- layout: bullets        # 2–4개
  items:
    - {icon: camera, text: CCTV 영상, sub: 얼굴로 개인을 알아볼 수 있습니다}
    - 아이콘 없이 문장만 써도 됨 (번호가 붙는다)
  illust: idea           # 선택

- layout: cards          # 2–3개
  highlight: 3           # 선택
  items:
    - {icon: user, title: 일반 정보, text: 성명 · 연락처 · 주소}

- layout: compare
  left:  {title: 개인정보 O, mark: O, items: [살아 있는 개인의 정보, 결합하면 식별되는 정보]}
  right: {title: 개인정보 X, mark: X, items: [법인 · 단체 자체의 정보]}

- layout: steps          # 2–4단계
  items:
    - {title: 수집, text: 필요한 최소한만, icon: download}   # icon 선택 (없으면 번호)

- layout: emphasis
  statement: "**알아볼 수 있다면** | 개인정보입니다"   # 최대 3줄
  sub: 애매할 때는 개인정보로 보고 보호하세요
  illust: idea           # 선택

- layout: quote
  source: 「개인정보 보호법」 제2조 제1호
  text: "**살아 있는 개인**에 관한 정보로서 …"    # 4줄 이하 36px, 넘으면 32px
  illust: document       # 선택 (넣으면 폭이 줄어든다)

- layout: stat
  caption: 법령으로 정한 고유식별정보
  value: 4
  unit: 종
  desc: 주민등록번호 · 여권번호 · 운전면허번호 · 외국인등록번호
  illust: id_card

- layout: case
  tag: 실제 유형
  heading: 메일 수신자 실수
  lines:
    - 고객 명단 파일을 다른 고객사 담당자에게 잘못 보냈습니다.
    - "**발송 전 수신자와 첨부를 다시 확인**하세요."
  illust: mail           # 기본 talk

- layout: screen
  image: shots/login.png # 선택 — YAML 기준 상대 경로. 없으면 깔끔한 UI 자리표시
  steps: [접근 권한은 필요한 사람만, 내려받은 파일은 암호화]   # 1–4개

- layout: quiz
  type: ox               # ox | choice
  question: 회사(법인)의 대표 전화번호는 개인정보이다.
  # type: choice → options: [보기1, 보기2, 보기3, 보기4]

- layout: answer
  question: 회사(법인)의 대표 전화번호는 개인정보이다.
  answer: X              # O | X | 보기 번호
  headline: 정답은 X
  explain:
    - 법인 · 단체 자체의 정보는 개인정보가 아닙니다.

- layout: summary        # 2–4개 (문장 또는 {text, sub})
  items: [살아 있는 개인을 알아볼 수 있으면 개인정보]
  illust: trophy

- layout: ending
  title: 수고하셨습니다
  sub: 다음 차시 · 개인정보 수집 · 이용 동의 받기
  illust: graduate       # 기본 trophy
```

## 맞지 않을 때

빌더는 내용을 몰래 자르지 않는다. 넘치면 `FIT ERRORS`에 슬라이드 번호와 이유를 출력하고 멈춘다. 이럴 때는 문장을 줄이거나, 화면을 둘로 나누거나, 더 넓은 레이아웃(cards → bullets, 일러스트 빼기)으로 바꾼다. 원고의 뜻이 달라지게 줄였다면 보고에 적는다.
