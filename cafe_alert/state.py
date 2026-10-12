"""이미 확인한 게시글 ID를 저장해 중복 알림을 막는다."""
from __future__ import annotations

import json
from pathlib import Path

MAX_IDS = 5000


class SeenStore:
    def __init__(self, path: Path):
        self.path = path
        self.exists = path.exists()
        self._ids: dict[str, None] = {}
        if self.exists:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._ids = dict.fromkeys(str(i) for i in data.get("seen", []))
            except (json.JSONDecodeError, OSError):
                self.exists = False

    def __contains__(self, article_id: str) -> bool:
        return str(article_id) in self._ids

    def add(self, article_id: str) -> None:
        self._ids.pop(str(article_id), None)
        self._ids[str(article_id)] = None

    def save(self) -> None:
        ids = list(self._ids)[-MAX_IDS:]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"seen": ids}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
        self.exists = True
