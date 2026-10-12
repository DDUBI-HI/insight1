import json
from pathlib import Path

import pytest

from cafe_alert.app import format_message, run_once
from cafe_alert.config import Config, Keywords, load_config
from cafe_alert.kakao import KakaoClient
from cafe_alert.matcher import Matcher
from cafe_alert.naver import Article, NaverCafeClient, parse_article_list, parse_search_items

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def cfg(tmp_path):
    c = load_config(ROOT / "config.yaml")
    c.club_id = "12345"
    c.cafe_url = "insacafe"
    c.state_file = tmp_path / "seen.json"
    c.token_file = tmp_path / "kakao_token.json"
    c.rotated_token_file = tmp_path / "rotated_refresh_token"
    c.kakao_rest_api_key = "rest-key"
    c.kakao_refresh_token = "rt-0"
    return c


# ---------- matcher ----------
@pytest.mark.parametrize(
    "title,body,expected",
    [
        ("팀장 리더십 교육 업체 추천 부탁드립니다", "", True),
        ("생성형 AI 사내 특강 강사님 찾습니다", "", True),
        ("ChatGPT 활용 교육 어디서 하시나요? 있을까요", "", True),
        ("교육 업체 추천 부탁드려요", "신임 팀장 대상 리더십 과정입니다", True),  # 본문 매칭
        ("리더십 교육 후기", "", False),                # 문의 의도 없음
        ("[채용] AI 교육 담당자 구인 문의", "", False),  # 제외어
        ("급여 메일 발송 문의", "", False),              # 'AI'가 'MAIL'/'메일'에 걸리지 않음
        ("연말정산 문의드립니다", "", False),            # 주제 없음
    ],
)
def test_matcher(cfg, title, body, expected):
    assert Matcher(cfg.keywords).match(title, body).matched is expected


def test_english_keyword_boundary():
    m = Matcher(Keywords(topics=["AI"], intents=[], require_intent=False))
    assert m.match("AI교육").matched          # 한글이 붙어도 매칭
    assert m.match("ai 강의").matched         # 대소문자 무시
    assert not m.match("EMAIL 설정").matched  # 영단어 내부는 제외


# ---------- naver parsing ----------
def test_parse_v2dot1(cfg):
    data = {"message": {"status": "200", "result": {"articleList": [
        {"articleId": 101, "subject": "리더십 &amp; 코칭 문의", "writerNickname": "hr팀장", "menuName": "자유게시판"},
        {"articleId": 100, "subject": "<b>old</b>"},
    ]}}}
    arts = parse_article_list(data, NaverCafeClient(cfg))
    assert [a.article_id for a in arts] == ["101", "100"]
    assert arts[0].title == "리더십 & 코칭 문의"
    assert arts[0].writer == "hr팀장"
    assert arts[0].url == "https://cafe.naver.com/insacafe/101"
    assert arts[1].title == "old"


def test_parse_boardlist_v1(cfg):
    data = {"result": {"articleList": [
        {"type": "ARTICLE", "item": {"articleId": 7, "subject": "AI 특강 문의", "writerInfo": {"nickName": "kim"},
                                     "menuName": "질문"}},
        {"type": "NOTICE_BANNER", "item": {}},
    ]}}
    arts = parse_article_list(data, NaverCafeClient(cfg))
    assert len(arts) == 1 and arts[0].writer == "kim" and arts[0].menu_name == "질문"


def test_parse_search_items_filters_other_cafes():
    data = {"items": [
        {"title": "<b>리더십</b> 교육", "link": "https://cafe.naver.com/insacafe/555", "description": "추천 부탁"},
        {"title": "다른 카페", "link": "https://cafe.naver.com/othercafe/1", "description": ""},
    ]}
    arts = parse_search_items(data, "insacafe")
    assert [a.article_id for a in arts] == ["555"]
    assert arts[0].title == "리더십 교육"


# ---------- app flow ----------
class FakeNaver:
    def __init__(self, articles, bodies=None):
        self.articles = articles
        self.bodies = bodies or {}

    def fetch_new_candidates(self):
        return list(self.articles)

    def fetch_body(self, aid):
        return self.bodies.get(aid, "")


class FakeKakao:
    def __init__(self):
        self.sent = []

    def send_text(self, text, link_url=None, button_title="글 보기"):
        self.sent.append((text, link_url))


def art(aid, title):
    return Article(article_id=str(aid), title=title, url=f"https://cafe.naver.com/insacafe/{aid}")


def test_first_run_bootstraps_without_flooding(cfg):
    kakao = FakeKakao()
    run_once(cfg, naver=FakeNaver([art(1, "리더십 교육 추천 부탁")]), kakao=kakao)
    assert len(kakao.sent) == 1 and "시작" in kakao.sent[0][0]
    assert json.loads(cfg.state_file.read_text())["seen"] == ["1"]


def test_only_new_matching_articles_are_sent(cfg):
    kakao = FakeKakao()
    run_once(cfg, naver=FakeNaver([art(1, "old")]), kakao=kakao)
    kakao.sent.clear()

    naver = FakeNaver(
        [art(1, "old"), art(3, "AI 특강 강사 섭외 문의"), art(2, "점심 메뉴 추천"), art(4, "업체 추천 부탁드립니다")],
        bodies={"4": "팀장 리더십 워크숍을 준비 중입니다"},
    )
    matched = run_once(cfg, naver=naver, kakao=kakao)
    assert [a.article_id for a in matched] == ["3", "4"]
    assert [link for _, link in kakao.sent] == [
        "https://cafe.naver.com/insacafe/3",
        "https://cafe.naver.com/insacafe/4",
    ]

    # 같은 글은 다시 보내지 않음
    kakao.sent.clear()
    run_once(cfg, naver=naver, kakao=kakao)
    assert kakao.sent == []


def test_overflow_is_summarized(cfg):
    cfg.max_notifications_per_run = 2
    kakao = FakeKakao()
    run_once(cfg, naver=FakeNaver([]), kakao=kakao)
    kakao.sent.clear()
    naver = FakeNaver([art(i, f"리더십 교육 문의 {i}") for i in range(10, 15)])
    run_once(cfg, naver=naver, kakao=kakao)
    assert len(kakao.sent) == 3
    assert "3건이 더" in kakao.sent[-1][0]


def test_send_failure_keeps_articles_unseen(cfg):
    run_once(cfg, naver=FakeNaver([]), kakao=FakeKakao())

    class Boom(FakeKakao):
        def send_text(self, *a, **k):
            raise RuntimeError("network")

    with pytest.raises(RuntimeError):
        run_once(cfg, naver=FakeNaver([art(5, "AI 교육 문의")]), kakao=Boom())
    kakao = FakeKakao()
    run_once(cfg, naver=FakeNaver([art(5, "AI 교육 문의")]), kakao=kakao)
    assert len(kakao.sent) == 1


def test_format_message_fits_kakao_limit(cfg):
    msg = format_message(cfg, Article("1", "가" * 300, "u", writer="w", menu_name="m"), ["AI"])
    assert msg.startswith("[인사쟁이] 새 교육 문의")


# ---------- kakao ----------
class FakeResp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.content = json.dumps(body).encode()

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.responses.pop(0)


def test_kakao_refresh_and_send_with_rotation(cfg):
    s = FakeSession([
        FakeResp(200, {"access_token": "at-1", "expires_in": 21599,
                       "refresh_token": "rt-1", "refresh_token_expires_in": 5184000}),
        FakeResp(200, {"result_code": 0}),
    ])
    k = KakaoClient(cfg, session=s)
    k.send_text("x" * 250, link_url="https://cafe.naver.com/insacafe/1")

    token_call, memo_call = s.calls
    assert token_call[1]["data"]["refresh_token"] == "rt-0"
    assert memo_call[1]["headers"]["Authorization"] == "Bearer at-1"
    tpl = json.loads(memo_call[1]["data"]["template_object"])
    assert len(tpl["text"]) == 200
    assert tpl["link"]["mobile_web_url"] == "https://cafe.naver.com/insacafe/1"
    assert cfg.rotated_token_file.read_text() == "rt-1"
    assert json.loads(cfg.token_file.read_text())["refresh_token"] == "rt-1"


def test_kakao_retries_once_on_401(cfg):
    s = FakeSession([
        FakeResp(200, {"access_token": "at-1", "expires_in": 21599}),
        FakeResp(401, {"code": -401}),
        FakeResp(200, {"access_token": "at-2", "expires_in": 21599}),
        FakeResp(200, {"result_code": 0}),
    ])
    KakaoClient(cfg, session=s).send_text("hi")
    assert s.calls[-1][1]["headers"]["Authorization"] == "Bearer at-2"
    assert not cfg.rotated_token_file.exists()
