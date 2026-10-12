"""카카오톡 '나에게 보내기' (Kakao REST API - talk/memo)."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

from .config import Config

log = logging.getLogger(__name__)

AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"
MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
TEXT_LIMIT = 200  # 텍스트 템플릿 최대 길이


class KakaoError(RuntimeError):
    pass


def authorize_url(cfg: Config) -> str:
    q = {
        "client_id": cfg.kakao_rest_api_key,
        "redirect_uri": cfg.kakao_redirect_uri,
        "response_type": "code",
        "scope": "talk_message",
    }
    return f"{AUTH_URL}?{urlencode(q)}"


class KakaoClient:
    def __init__(self, cfg: Config, session: requests.Session | None = None):
        if not cfg.kakao_rest_api_key:
            raise KakaoError("KAKAO_REST_API_KEY 환경변수가 필요합니다.")
        self.cfg = cfg
        self.s = session or requests.Session()
        self.token_file: Path = cfg.token_file
        self.tokens = self._load_tokens()

    # ---------- 토큰 ----------
    def _load_tokens(self) -> dict:
        tokens: dict = {}
        if self.token_file.exists():
            try:
                tokens = json.loads(self.token_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                tokens = {}
        # 환경변수(예: GitHub Secret)의 refresh token은 파일이 없을 때만 사용
        if not tokens.get("refresh_token") and self.cfg.kakao_refresh_token:
            tokens["refresh_token"] = self.cfg.kakao_refresh_token
        return tokens

    def _save_tokens(self) -> None:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(json.dumps(self.tokens), encoding="utf-8")
        try:
            self.token_file.chmod(0o600)
        except OSError:
            pass

    def _token_request(self, data: dict) -> dict:
        data = {"client_id": self.cfg.kakao_rest_api_key, **data}
        if self.cfg.kakao_client_secret:
            data["client_secret"] = self.cfg.kakao_client_secret
        r = self.s.post(TOKEN_URL, data=data, timeout=15)
        body = r.json() if r.content else {}
        if r.status_code != 200 or "access_token" not in body:
            raise KakaoError(f"토큰 발급 실패: {r.status_code} {body.get('error')} {body.get('error_description')}")
        return body

    def exchange_code(self, code: str) -> None:
        body = self._token_request(
            {"grant_type": "authorization_code", "redirect_uri": self.cfg.kakao_redirect_uri, "code": code}
        )
        self._apply(body, rotated=False)

    def refresh(self) -> None:
        rt = self.tokens.get("refresh_token")
        if not rt:
            raise KakaoError("refresh token이 없습니다. `python -m cafe_alert kakao-auth`로 먼저 인증하세요.")
        body = self._token_request({"grant_type": "refresh_token", "refresh_token": rt})
        self._apply(body, rotated="refresh_token" in body)

    def _apply(self, body: dict, rotated: bool) -> None:
        self.tokens["access_token"] = body["access_token"]
        self.tokens["expires_at"] = int(time.time()) + int(body.get("expires_in", 21599)) - 60
        if "refresh_token" in body:
            self.tokens["refresh_token"] = body["refresh_token"]
            if "refresh_token_expires_in" in body:
                self.tokens["refresh_expires_at"] = int(time.time()) + int(body["refresh_token_expires_in"])
        self._save_tokens()
        if rotated:
            # 카카오는 refresh token 만료 1개월 전부터 갱신 시 새 토큰을 준다.
            # GitHub Actions에서는 이 파일을 보고 Secret을 갱신한다.
            self.cfg.rotated_token_file.parent.mkdir(parents=True, exist_ok=True)
            self.cfg.rotated_token_file.write_text(body["refresh_token"], encoding="utf-8")
            log.info("카카오 refresh token이 갱신되었습니다.")

    def access_token(self) -> str:
        if not self.tokens.get("access_token") or self.tokens.get("expires_at", 0) <= time.time():
            self.refresh()
        return self.tokens["access_token"]

    # ---------- 전송 ----------
    def send_text(self, text: str, link_url: str | None = None, button_title: str = "글 보기") -> None:
        if len(text) > TEXT_LIMIT:
            text = text[: TEXT_LIMIT - 1] + "…"
        template = {"object_type": "text", "text": text, "link": {}}
        if link_url:
            template["link"] = {"web_url": link_url, "mobile_web_url": link_url}
            template["button_title"] = button_title
        payload = {"template_object": json.dumps(template, ensure_ascii=False)}

        for attempt in range(2):
            r = self.s.post(
                MEMO_URL,
                headers={"Authorization": f"Bearer {self.access_token()}"},
                data=payload,
                timeout=15,
            )
            if r.status_code == 401 and attempt == 0:
                self.tokens.pop("access_token", None)  # 만료 → 재발급 후 1회 재시도
                continue
            body = r.json() if r.content else {}
            if r.status_code != 200 or body.get("result_code") != 0:
                raise KakaoError(f"카카오톡 전송 실패: {r.status_code} {body}")
            return
