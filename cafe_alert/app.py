"""한 번의 점검 사이클: 새 글 수집 → 키워드 필터 → 카카오톡 전송 → 상태 저장."""
from __future__ import annotations

import logging

from .config import Config
from .kakao import KakaoClient
from .matcher import Matcher
from .naver import Article, NaverCafeClient
from .state import SeenStore

log = logging.getLogger(__name__)


def format_message(cfg: Config, article: Article, topics: list[str]) -> str:
    lines = [f"[{cfg.cafe_name}] 새 교육 문의"]
    if article.menu_name:
        lines.append(f"게시판: {article.menu_name}")
    lines.append(f"제목: {article.title}")
    if article.writer:
        lines.append(f"작성자: {article.writer}")
    if topics:
        lines.append(f"키워드: {', '.join(topics[:5])}")
    return "\n".join(lines)


def run_once(cfg: Config, dry_run: bool = False, naver: NaverCafeClient | None = None,
             kakao: KakaoClient | None = None) -> list[Article]:
    naver = naver or NaverCafeClient(cfg)
    matcher = Matcher(cfg.keywords)
    seen = SeenStore(cfg.state_file)
    if kakao is None and not dry_run:
        kakao = KakaoClient(cfg)

    articles = naver.fetch_new_candidates()
    log.info("게시글 %d건 수집", len(articles))

    # 최초 실행: 기존 글은 모두 '본 것'으로 처리해서 알림 폭탄을 막는다.
    if not seen.exists:
        for a in articles:
            seen.add(a.article_id)
        if not dry_run:
            seen.save()
            if cfg.notify_on_start and kakao:
                kakao.send_text(
                    f"[{cfg.cafe_name}] 교육 문의 알림을 시작합니다.\n"
                    f"기존 글 {len(articles)}건은 건너뛰고, 이후 새 글부터 알려드릴게요."
                )
        log.info("최초 실행: 기존 글 %d건을 기준점으로 저장했습니다.", len(articles))
        return []

    # 오래된 글부터 알림이 가도록 ID 오름차순
    new = sorted((a for a in articles if a.article_id not in seen),
                 key=lambda a: int(a.article_id) if a.article_id.isdigit() else 0)
    matched: list[tuple[Article, list[str]]] = []
    for a in new:
        if cfg.check_body and cfg.source == "cafe_api" and not a.body:
            a.body = naver.fetch_body(a.article_id)
        result = matcher.match(a.title, a.body)
        # 공개 저장소의 Actions 로그는 누구나 볼 수 있으므로 글 제목은 DEBUG(-v)에서만 출력
        log.debug("%s %s | topics=%s intents=%s exclude=%s",
                 "✔" if result.matched else "·", a.title, result.topics, result.intents, result.excluded_by)
        if result.matched:
            matched.append((a, result.topics))

    limit = max(cfg.max_notifications_per_run, 1)
    for a, topics in matched[:limit]:
        text = format_message(cfg, a, topics)
        if dry_run:
            print(f"--- (dry-run) 카톡 메시지 ---\n{text}\n{a.url}\n")
        else:
            kakao.send_text(text, link_url=a.url)

    if len(matched) > limit:
        rest = matched[limit:]
        text = f"[{cfg.cafe_name}] 교육 문의 {len(rest)}건이 더 있습니다.\n" + "\n".join(
            f"- {a.title}" for a, _ in rest[:5]
        )
        if dry_run:
            print(text)
        else:
            kakao.send_text(text, link_url=rest[0][0].url, button_title="카페 열기")

    # 전송이 끝난 뒤에 저장 (전송 실패 시 다음 실행에서 다시 시도)
    if not dry_run:
        for a in new:
            seen.add(a.article_id)
        seen.save()

    log.info("새 글 %d건 중 교육 문의 %d건", len(new), len(matched))
    return [a for a, _ in matched]
