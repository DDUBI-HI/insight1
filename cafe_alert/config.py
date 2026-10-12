"""설정 로딩: config.yaml(공개 가능한 설정) + 환경변수/.env(비밀값)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    """간단한 .env 로더. 이미 설정된 환경변수는 덮어쓰지 않는다."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass
class Keywords:
    topics: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    require_intent: bool = True


@dataclass
class Config:
    # 카페
    cafe_name: str = "인사쟁이"
    cafe_url: str = ""          # cafe.naver.com/<cafe_url>
    club_id: str = ""           # 숫자 카페 ID
    menu_ids: list[int] = field(default_factory=list)  # 비우면 전체글
    source: str = "cafe_api"    # cafe_api | search_api
    search_queries: list[str] = field(default_factory=list)
    check_body: bool = True
    per_page: int = 50

    # 필터
    keywords: Keywords = field(default_factory=Keywords)

    # 알림
    max_notifications_per_run: int = 10
    notify_on_start: bool = True

    # 경로
    state_file: Path = ROOT / "data" / "seen.json"
    token_file: Path = ROOT / "data" / "kakao_token.json"
    rotated_token_file: Path = ROOT / "data" / "rotated_refresh_token"

    # 비밀값 (환경변수)
    kakao_rest_api_key: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = ""
    kakao_refresh_token: str = ""
    naver_nid_aut: str = ""
    naver_nid_ses: str = ""
    naver_client_id: str = ""
    naver_client_secret: str = ""


def load_config(path: str | os.PathLike | None = None) -> Config:
    load_dotenv(ROOT / ".env")

    cfg_path = Path(path) if path else Path(os.environ.get("CAFE_ALERT_CONFIG", ROOT / "config.yaml"))
    raw: dict = {}
    if cfg_path.exists():
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    cafe = raw.get("cafe", {}) or {}
    kw = raw.get("keywords", {}) or {}
    notify = raw.get("notify", {}) or {}

    cfg = Config(
        cafe_name=str(cafe.get("name", "인사쟁이")),
        cafe_url=str(cafe.get("url", "") or "").strip().rstrip("/").split("/")[-1],
        club_id=str(os.environ.get("NAVER_CAFE_CLUB_ID") or cafe.get("club_id", "") or "").strip(),
        menu_ids=[int(m) for m in (cafe.get("menu_ids") or [])],
        source=str(cafe.get("source", "cafe_api")),
        search_queries=list(cafe.get("search_queries") or []),
        check_body=bool(cafe.get("check_body", True)),
        per_page=int(cafe.get("per_page", 50)),
        keywords=Keywords(
            topics=list(kw.get("topics") or []),
            intents=list(kw.get("intents") or []),
            exclude=list(kw.get("exclude") or []),
            require_intent=bool(kw.get("require_intent", True)),
        ),
        max_notifications_per_run=int(notify.get("max_per_run", 10)),
        notify_on_start=bool(notify.get("on_start", True)),
        kakao_rest_api_key=os.environ.get("KAKAO_REST_API_KEY", ""),
        kakao_client_secret=os.environ.get("KAKAO_CLIENT_SECRET", ""),
        kakao_redirect_uri=os.environ.get("KAKAO_REDIRECT_URI", "https://localhost"),
        kakao_refresh_token=os.environ.get("KAKAO_REFRESH_TOKEN", ""),
        naver_nid_aut=os.environ.get("NAVER_NID_AUT", ""),
        naver_nid_ses=os.environ.get("NAVER_NID_SES", ""),
        naver_client_id=os.environ.get("NAVER_CLIENT_ID", ""),
        naver_client_secret=os.environ.get("NAVER_CLIENT_SECRET", ""),
    )

    data_dir = os.environ.get("CAFE_ALERT_DATA_DIR")
    if data_dir:
        d = Path(data_dir)
        cfg.state_file = d / "seen.json"
        cfg.token_file = d / "kakao_token.json"
        cfg.rotated_token_file = d / "rotated_refresh_token"
    return cfg
