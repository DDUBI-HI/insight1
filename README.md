# 인사쟁이 카페 교육 문의 → 카카오톡 알림

네이버 카페 **'인사쟁이'**에 리더십·AI 등 **기업교육 문의 글**이 올라오면 내 카카오톡(**나와의 채팅**)으로 알려주는 자동화입니다.

```
GitHub Actions (10분마다)
   └─ 네이버 카페 새 글 조회 ──► 키워드 필터 ──► 카카오톡 "나에게 보내기"
        (cafe_api / search_api)   (주제 + 문의의도 − 제외어)   (글 링크 버튼 포함)
```

- **중복 알림 없음**: 확인한 글 ID를 저장하고, 첫 실행 때는 기존 글을 건너뜁니다.
- **본문 검사**: 제목이 "업체 추천 부탁드려요"처럼 모호해도, 본문에 '리더십' 등이 있으면 잡습니다.
- **키워드 조정**: `config.yaml`만 고치면 됩니다.
- **비용 0원**: 공개 저장소의 GitHub Actions는 무료입니다. PC나 서버에서 상시 실행해도 됩니다.

받게 되는 메시지 예시:

```
[인사쟁이] 새 교육 문의
게시판: 교육/강사 추천
제목: 신임 팀장 리더십 교육 업체 추천 부탁드립니다
작성자: HR담당자
키워드: 리더십, 팀장, 신임
                       [ 글 보기 ]
```

---

## 1. 카카오톡 설정 (최초 1회, 약 10분)

1. [Kakao Developers](https://developers.kakao.com)에 로그인 → **내 애플리케이션 → 애플리케이션 추가하기**
2. **앱 키**에서 **REST API 키**를 복사합니다.
3. **카카오 로그인**에서 *활성화 설정*을 **ON**으로 바꾸고, **Redirect URI**에 `https://localhost`를 등록합니다.
4. **카카오 로그인 → 동의항목**에서 **카카오톡 메시지 전송(talk_message)**을 *선택 동의*로 설정합니다.
5. **플랫폼 → Web → 사이트 도메인**에 `https://cafe.naver.com`을 추가합니다. 빠뜨리면 알림의 '글 보기' 버튼이 열리지 않습니다.
6. (선택) **카카오 로그인 → 보안**에서 Client Secret을 *사용함*으로 했다면 그 값도 복사해 둡니다.

그다음 토큰을 발급합니다.

```bash
pip install -r requirements.txt
cp .env.example .env          # KAKAO_REST_API_KEY (와 KAKAO_CLIENT_SECRET) 입력

python -m cafe_alert kakao-auth-url
# 출력된 URL을 브라우저로 열고 동의합니다.
# https://localhost/?code=XXXX 로 이동하면서 '사이트에 연결할 수 없음'이 떠도 정상입니다.
# 주소창에서 code= 뒤의 값을 복사합니다.

python -m cafe_alert kakao-auth --code XXXX
python -m cafe_alert test-kakao     # 카톡 '나와의 채팅'에 테스트 메시지가 오면 성공
```

`kakao-auth` 실행 결과에 나오는 **refresh token**은 GitHub Actions에서 씁니다.

## 2. 카페 설정

`config.yaml`의 `cafe` 항목을 채웁니다.

| 항목 | 설명 |
|---|---|
| `url` | 카페 주소의 마지막 부분 (`https://cafe.naver.com/xxxx` → `xxxx`) |
| `club_id` | 숫자 카페 ID. `python -m cafe_alert resolve-clubid xxxx`로 확인합니다. |
| `menu_ids` | 교육 문의 게시판처럼 특정 게시판만 볼 때 입력합니다. 비우면 전체글을 봅니다. |
| `source` | `cafe_api`(권장) 또는 `search_api` |

**수동으로 club_id 찾기**: PC에서 카페의 아무 게시판이나 클릭한 뒤 주소나 페이지 소스에서 `clubid=숫자`를 찾습니다. 이때 `menuid=숫자`가 게시판 ID입니다.

### 회원만 글을 볼 수 있는 카페라면 (cafe_api + 로그인 쿠키)

카페에 가입된 계정으로 PC 브라우저에서 네이버에 로그인합니다. 그다음 `F12` → **Application(애플리케이션) → Cookies → https://naver.com**에서 `NID_AUT`, `NID_SES` 값을 복사해 `.env`(또는 GitHub Secrets)에 넣습니다.

> ⚠️ 이 쿠키는 **네이버 계정 비밀번호와 같은 수준의 정보**입니다. 절대 `config.yaml`에 쓰거나 커밋하지 마세요. 브라우저에서 **로그아웃하면 쿠키가 무효화**되므로, 쿠키를 뽑은 브라우저는 로그아웃하지 말고 창만 닫으세요. 가능하면 알림 전용 부계정을 쓰는 것이 안전합니다.

### 로그인 없이 쓰려면 (search_api)

[네이버 개발자센터](https://developers.naver.com/apps)에서 애플리케이션을 등록하고 **검색** API를 선택합니다. 발급받은 `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`를 넣고 `source: search_api`로 바꿉니다. 단, 네이버 검색에 노출되는 **전체공개 글만** 잡히고 반영이 다소 늦을 수 있습니다.

## 3. 실행

### A. 로컬 PC / 서버에서

```bash
python -m cafe_alert run --dry-run     # 카톡 전송 없이 어떤 글이 걸리는지 확인
python -m cafe_alert run               # 1회 실행 (cron/작업 스케줄러에 등록)
python -m cafe_alert run --loop 300    # 5분마다 계속 실행
```

### B. GitHub Actions (PC를 켜 둘 필요 없음, 권장)

저장소 **Settings → Secrets and variables → Actions**에서 아래 값을 등록합니다.

| 종류 | 이름 | 값 |
|---|---|---|
| Secret | `KAKAO_REST_API_KEY` | 카카오 REST API 키 |
| Secret | `KAKAO_REFRESH_TOKEN` | `kakao-auth` 실행 결과로 받은 refresh token |
| Secret | `KAKAO_CLIENT_SECRET` | (사용 시) Client Secret |
| Secret | `NAVER_NID_AUT`, `NAVER_NID_SES` | (회원 전용 카페) 로그인 쿠키 |
| Secret | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | (search_api 모드) |
| Secret | `GH_PAT` | (권장) 토큰 자동 갱신용. 아래 참고 |
| Variable | `NAVER_CAFE_CLUB_ID` | config.yaml 대신 여기에 club_id를 넣어도 됩니다. |

`config.yaml`의 카페 정보를 커밋한 뒤 **Actions → 카페 교육문의 알림 → Run workflow**로 먼저 수동 실행해 봅니다(`dry_run` 체크 가능). 이후에는 10분마다 자동으로 실행됩니다. `KAKAO_REST_API_KEY`가 등록되기 전에는 아무 동작도 하지 않습니다.

**토큰 자동 갱신 (GH_PAT)**: 카카오 refresh token은 **2개월** 동안 유효하고, 만료 1개월 전부터는 새 토큰으로 교체됩니다. 이 교체된 토큰을 Secret에 자동 저장하려면 GitHub **Settings → Developer settings → Fine-grained tokens**에서 토큰을 만듭니다. 이 저장소만 선택하고 *Secrets: Read and write* 권한을 준 뒤, 그 토큰을 `GH_PAT` Secret으로 등록합니다. 등록하지 않으면 약 2개월마다 `kakao-auth`를 다시 실행해 Secret을 직접 바꿔야 합니다. 실행이 실패하면 GitHub가 메일로 알려줍니다.

> ℹ️ 이 저장소는 **공개(public)** 저장소라서 Actions 로그를 누구나 볼 수 있습니다. 그래서 기본 로그에는 글 제목 없이 건수만 남깁니다. 비밀값은 Secrets에만 두면 로그에 노출되지 않습니다.

## 4. 키워드 조정

`config.yaml`의 `keywords`를 고칩니다.

- `topics`: 이 중 **하나 이상** 있어야 합니다 (리더십, AI, 기업교육 …).
- `intents`: `require_intent: true`이면 이 중 하나도 있어야 합니다 (문의, 추천, 강사, 업체 …). 단순 정보글이나 후기를 걸러냅니다.
- `exclude`: **제목**에 이 단어가 있으면 제외합니다 (채용, 홍보 …).

영문 키워드는 단어 단위로 매칭됩니다. 그래서 `AI`가 `EMAIL` 같은 단어에 섞여 잘못 걸리지 않습니다. 원하는 글이 걸리는지는 바로 시험해 볼 수 있습니다.

```bash
python -m cafe_alert check "생성형 AI 사내 특강 강사님 찾습니다"
```

## 5. 알아둘 점

- `cafe_api`는 네이버 카페 웹이 내부적으로 쓰는 **비공식 API**입니다. 네이버가 형식을 바꾸면 수정이 필요할 수 있습니다. 실행이 실패하면 Actions 로그와 GitHub 실패 메일로 알 수 있습니다.
- 해외(GitHub 서버) IP에서 로그인 쿠키를 쓰면 네이버가 보안 확인을 요구하거나 세션을 끊을 수 있습니다. 쿠키 방식이 자주 끊기면 국내 PC/서버에서 `--loop`로 실행하거나 `search_api` 모드를 쓰세요.
- 카페 이용 규칙을 지켜 주세요. 이 도구는 **본인 열람 목적의 알림**용입니다. 수집한 글을 재게시하거나 짧은 간격으로 과도하게 요청하지 마세요.

## 개발

```bash
pip install pytest
python -m pytest -q
```

```
cafe_alert/
  config.py   설정 로딩 (config.yaml + .env/환경변수)
  naver.py    카페 글 목록/본문 조회, 검색 API, club_id 조회
  matcher.py  키워드 필터
  kakao.py    카카오 토큰 발급·갱신, 나에게 보내기
  state.py    확인한 글 ID 저장
  app.py      1회 점검 흐름
.github/workflows/cafe-alert.yml   10분 주기 실행
```
