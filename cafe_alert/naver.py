"""네이버 카페 게시글 수집.

두 가지 방식을 지원한다.
- cafe_api  : 카페 웹이 내부적으로 쓰는 게시글 목록 API. 회원 전용 게시판은 로그인 쿠키(NID_AUT, NID_SES)가 필요.
- search_api: 네이버 공식 검색 API(카페글). 로그인 불필요, 단 검색에 노출되는(전체공개) 글만 잡힌다.

카페 내부 API는 비공식이라 응답 형식이 바뀔 수 있어 파싱을 느슨하게 했다.
"""
from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass, field

import requests

from .config import Config

log = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
LIST_V2 = "https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json"
LIST_V1_BOARD = "https://apis.naver.com/cafe-web/cafe-boardlist-api/v1/cafes/{club_id}/menus/{menu_id}/articles"
ARTICLE_DETAIL = "https://apis.naver.com/cafe-web/cafe-articleapi/v2.1/cafes/{club_id}/articles/{article_id}"
GATE_INFO = "https://apis.naver.com/cafe-web/cafe2/CafeGateInfo.json"
SEARCH_API = "https://openapi.naver.com/v1/search/cafearticle.json"

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


@dataclass
class Article:
    article_id: str
    title: str
    url: str
    writer: str = ""
    menu_name: str = ""
    body: str = ""
    extra: dict = field(default_factory=dict)


class NaverCafeClient:
    def __init__(self, cfg: Config, session: requests.Session | None = None):
        self.cfg = cfg
        self.s = session or requests.Session()
        self.s.headers.update({"User-Agent": UA, "Referer": "https://cafe.naver.com/"})
        if cfg.naver_nid_aut and cfg.naver_nid_ses:
            for name, value in (("NID_AUT", cfg.naver_nid_aut), ("NID_SES", cfg.naver_nid_ses)):
                self.s.cookies.set(name, value, domain=".naver.com")

    # ---------- 공통 ----------
    def article_url(self, article_id: str) -> str:
        if self.cfg.cafe_url:
            return f"https://cafe.naver.com/{self.cfg.cafe_url}/{article_id}"
        return f"https://cafe.naver.com/ca-fe/cafes/{self.cfg.club_id}/articles/{article_id}"

    def fetch_new_candidates(self) -> list[Article]:
        if self.cfg.source == "search_api":
            return self._search_api()
        if not self.cfg.club_id:
            raise RuntimeError(
                "config.yaml의 cafe.club_id가 비어 있습니다. "
                "`python -m cafe_alert resolve-clubid <카페주소>`로 확인하세요."
            )
        menus = self.cfg.menu_ids or [0]
        out: dict[str, Article] = {}
        for menu_id in menus:
            for a in self._cafe_list(menu_id):
                out.setdefault(a.article_id, a)
        return list(out.values())

    # ---------- cafe_api ----------
    def _cafe_list(self, menu_id: int) -> list[Article]:
        params = {
            "search.clubid": self.cfg.club_id,
            "search.queryType": "lastArticle",
            "search.page": 1,
            "search.perPage": self.cfg.per_page,
        }
        if menu_id:
            params["search.menuid"] = menu_id
        try:
            r = self.s.get(LIST_V2, params=params, timeout=15)
            r.raise_for_status()
            articles = parse_article_list(r.json(), self)
            if articles:
                return articles
            log.info("ArticleListV2dot1 응답에 글이 없어 신규 목록 API를 시도합니다.")
        except (requests.RequestException, ValueError) as e:
            log.warning("ArticleListV2dot1 실패(%s), 신규 목록 API로 재시도합니다.", e)

        r = self.s.get(
            LIST_V1_BOARD.format(club_id=self.cfg.club_id, menu_id=menu_id),
            params={"page": 1, "pageSize": self.cfg.per_page, "sortBy": "TIME", "viewType": "L"},
            timeout=15,
        )
        r.raise_for_status()
        return parse_article_list(r.json(), self)

    def fetch_body(self, article_id: str) -> str:
        try:
            r = self.s.get(
                ARTICLE_DETAIL.format(club_id=self.cfg.club_id, article_id=article_id),
                params={"useCafeId": "true", "requestFrom": "A"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            log.info("본문 조회 실패(%s): %s", article_id, e)
            return ""
        art = (data.get("result") or {}).get("article") or {}
        return strip_html(art.get("contentHtml") or art.get("content") or "")

    # ---------- search_api ----------
    def _search_api(self) -> list[Article]:
        if not (self.cfg.naver_client_id and self.cfg.naver_client_secret):
            raise RuntimeError("search_api 모드에는 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 필요합니다.")
        if not self.cfg.cafe_url:
            raise RuntimeError("search_api 모드에는 config.yaml의 cafe.url(카페 주소)이 필요합니다.")
        headers = {
            "X-Naver-Client-Id": self.cfg.naver_client_id,
            "X-Naver-Client-Secret": self.cfg.naver_client_secret,
        }
        queries = self.cfg.search_queries or self.cfg.keywords.topics
        out: dict[str, Article] = {}
        for q in queries:
            r = requests.get(
                SEARCH_API,
                params={"query": f"{self.cfg.cafe_name} {q}", "display": 100, "sort": "date"},
                headers=headers,
                timeout=15,
            )
            r.raise_for_status()
            for a in parse_search_items(r.json(), self.cfg.cafe_url):
                out.setdefault(a.article_id, a)
        return list(out.values())


def _first(d: dict, *keys, default=""):
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return default


def parse_article_list(data: dict, client: NaverCafeClient) -> list[Article]:
    """구(V2dot1)/신(boardlist v1) 목록 API 응답을 모두 처리한다."""
    result = (data.get("message") or {}).get("result") or data.get("result") or {}
    raw_list = result.get("articleList") or []
    articles = []
    for entry in raw_list:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") and entry.get("type") != "ARTICLE":
            continue
        item = entry.get("item") or entry
        aid = _first(item, "articleId", "articleid")
        if not aid:
            continue
        writer_info = item.get("writerInfo") or {}
        articles.append(
            Article(
                article_id=str(aid),
                title=strip_html(str(_first(item, "subject", "title"))),
                url=client.article_url(str(aid)),
                writer=str(_first(item, "writerNickname", "nickname") or writer_info.get("nickName", "")),
                menu_name=strip_html(str(_first(item, "menuName"))),
            )
        )
    return articles


_ARTICLE_ID_RE = re.compile(r"cafe\.naver\.com/([^/?#]+)/(\d+)")


def parse_search_items(data: dict, cafe_url: str) -> list[Article]:
    out = []
    for it in data.get("items") or []:
        m = _ARTICLE_ID_RE.search(it.get("link", ""))
        if not m or m.group(1).lower() != cafe_url.lower():
            continue
        out.append(
            Article(
                article_id=m.group(2),
                title=strip_html(it.get("title", "")),
                url=f"https://cafe.naver.com/{m.group(1)}/{m.group(2)}",
                body=strip_html(it.get("description", "")),
            )
        )
    return out


def resolve_club_id(cafe_url: str, session: requests.Session | None = None) -> str | None:
    """카페 주소(cafe.naver.com/xxxx)로 숫자 club_id를 찾는다."""
    s = session or requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": "https://cafe.naver.com/"})
    slug = cafe_url.strip().rstrip("/").split("/")[-1]
    try:
        r = s.get(GATE_INFO, params={"cluburl": slug}, timeout=15)
        info = ((r.json().get("message") or {}).get("result") or {}).get("cafeInfoView") or {}
        if info.get("cafeId"):
            return str(info["cafeId"])
    except (requests.RequestException, ValueError):
        pass
    r = s.get(f"https://cafe.naver.com/{slug}", timeout=15)
    for pat in (r"clubid=(\d+)", r"g_sClubId\s*=\s*\"?(\d+)", r"\"cafeId\"\s*:\s*(\d+)"):
        m = re.search(pat, r.text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None
