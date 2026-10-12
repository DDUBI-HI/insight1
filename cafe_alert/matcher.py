"""게시글이 '기업교육 문의'인지 키워드로 판별한다."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .config import Keywords


def _compile(keyword: str) -> re.Pattern:
    """영문 키워드(AI, DX 등)는 다른 영단어 안에 섞여 매칭되지 않도록 경계를 둔다.

    한글은 조사가 붙으므로(예: '리더십교육', 'AI를') 부분 일치로 둔다.
    """
    escaped = re.escape(keyword.strip())
    if re.fullmatch(r"[A-Za-z0-9 .+#-]+", keyword.strip()):
        return re.compile(rf"(?<![A-Za-z]){escaped}(?![A-Za-z])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


@dataclass
class MatchResult:
    matched: bool
    topics: list[str]
    intents: list[str]
    excluded_by: list[str]


class Matcher:
    def __init__(self, keywords: Keywords):
        self.kw = keywords
        self._topics = [(k, _compile(k)) for k in keywords.topics if k.strip()]
        self._intents = [(k, _compile(k)) for k in keywords.intents if k.strip()]
        self._exclude = [(k, _compile(k)) for k in keywords.exclude if k.strip()]

    @staticmethod
    def _find(patterns, text: str) -> list[str]:
        return [k for k, p in patterns if p.search(text)]

    def match(self, title: str, body: str = "") -> MatchResult:
        text = f"{title}\n{body}"
        excluded = self._find(self._exclude, title)  # 제외어는 제목 기준(본문까지 보면 오탐 제외가 많음)
        topics = self._find(self._topics, text)
        intents = self._find(self._intents, text)
        ok = bool(topics) and not excluded
        if self.kw.require_intent:
            ok = ok and bool(intents)
        return MatchResult(ok, topics, intents, excluded)
