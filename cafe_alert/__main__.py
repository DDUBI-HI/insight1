"""CLI 진입점: python -m cafe_alert <명령>"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from .app import run_once
from .config import load_config
from .kakao import KakaoClient, authorize_url
from .matcher import Matcher
from .naver import resolve_club_id


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cafe_alert", description="네이버 카페 교육 문의 → 카카오톡 알림")
    p.add_argument("--config", help="설정 파일 경로 (기본: config.yaml)")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="새 글을 확인하고 알림 전송")
    r.add_argument("--dry-run", action="store_true", help="카톡 전송/상태 저장 없이 결과만 출력")
    r.add_argument("--loop", type=int, metavar="SECONDS", help="지정한 초마다 반복 실행 (PC/서버 상시 실행용)")

    sub.add_parser("kakao-auth-url", help="카카오 인가 코드 발급 URL 출력")
    a = sub.add_parser("kakao-auth", help="인가 코드로 토큰 발급")
    a.add_argument("--code", required=True)
    sub.add_parser("test-kakao", help="카카오톡 테스트 메시지 전송")

    c = sub.add_parser("resolve-clubid", help="카페 주소로 club_id 조회")
    c.add_argument("cafe_url")

    t = sub.add_parser("check", help="제목/본문이 필터에 걸리는지 테스트")
    t.add_argument("title")
    t.add_argument("body", nargs="?", default="")

    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    cfg = load_config(args.config)
    try:
        return _dispatch(args, cfg)
    except RuntimeError as e:  # 설정 누락, 카카오 인증 오류 등은 traceback 대신 메시지로
        logging.error("%s", e)
        return 1


def _dispatch(args, cfg) -> int:
    if args.cmd == "run":
        if not args.loop:
            run_once(cfg, dry_run=args.dry_run)
            return 0
        while True:
            try:
                run_once(cfg, dry_run=args.dry_run)
            except Exception:  # 상시 실행 중에는 한 번의 실패로 멈추지 않는다
                logging.exception("점검 중 오류")
            time.sleep(args.loop)

    if args.cmd == "kakao-auth-url":
        print(authorize_url(cfg))
        print("\n위 URL을 브라우저에서 열고 동의 → 이동된 주소의 code= 뒤 값을 복사해서")
        print("  python -m cafe_alert kakao-auth --code <값>")
        return 0

    if args.cmd == "kakao-auth":
        k = KakaoClient(cfg)
        k.exchange_code(args.code)
        print(f"토큰 저장 완료: {cfg.token_file}")
        print("GitHub Actions를 쓸 경우 아래 refresh token을 KAKAO_REFRESH_TOKEN Secret에 등록하세요:")
        print(k.tokens["refresh_token"])
        return 0

    if args.cmd == "test-kakao":
        KakaoClient(cfg).send_text(f"[{cfg.cafe_name}] 카카오톡 알림 테스트입니다 ✅",
                                   link_url="https://cafe.naver.com/" + (cfg.cafe_url or ""))
        print("전송 완료. 카카오톡 '나와의 채팅'을 확인하세요.")
        return 0

    if args.cmd == "resolve-clubid":
        club_id = resolve_club_id(args.cafe_url)
        if not club_id:
            print("club_id를 찾지 못했습니다. README의 '수동으로 club_id 찾기'를 참고하세요.")
            return 1
        print(club_id)
        return 0

    if args.cmd == "check":
        res = Matcher(cfg.keywords).match(args.title, args.body)
        print(f"매칭: {'예' if res.matched else '아니오'}")
        print(f"  주제 키워드: {res.topics}\n  문의 키워드: {res.intents}\n  제외 키워드: {res.excluded_by}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
