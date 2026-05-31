import hashlib
import json
from typing import Any, Dict, List, Optional

import redis

from config import Config


class RedisCache:
    """
    Redis cache wrapper.

    If Redis is not available, the class falls back silently.
    This makes the demo easier to run for interview display.
    """

    def __init__(self):
        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            self.client.ping()
            self.enabled = True
        except Exception:
            self.client = None
            self.enabled = False

    @staticmethod
    def _question_hash(question: str) -> str:
        return hashlib.md5(question.strip().lower().encode("utf-8")).hexdigest()

    def _answer_key(self, paper_id: str, question: str) -> str:
        return f"rag:answer:{paper_id}:{self._question_hash(question)}"

    def _history_key(self, paper_id: str) -> str:
        return f"rag:history:{paper_id}"

    def get_answer(self, paper_id: str, question: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None

        raw = self.client.get(self._answer_key(paper_id, question))
        return json.loads(raw) if raw else None

    def set_answer(
        self,
        paper_id: str,
        question: str,
        answer: str,
        sources: List[Dict[str, Any]],
    ) -> None:
        if not self.enabled:
            return

        payload = {
            "answer": answer,
            "sources": sources,
        }

        self.client.setex(
            self._answer_key(paper_id, question),
            Config.CACHE_EXPIRE_SECONDS,
            json.dumps(payload, ensure_ascii=False),
        )

    def get_history(self, paper_id: str) -> List[Dict[str, str]]:
        if not self.enabled:
            return []

        key = self._history_key(paper_id)
        items = self.client.lrange(key, 0, Config.MAX_HISTORY_ROUNDS - 1)
        history = []
        for item in items:
            try:
                history.append(json.loads(item))
            except json.JSONDecodeError:
                continue

        return list(reversed(history))

    def append_history(self, paper_id: str, question: str, answer: str) -> None:
        if not self.enabled:
            return

        key = self._history_key(paper_id)
        item = json.dumps(
            {"question": question, "answer": answer},
            ensure_ascii=False,
        )

        self.client.lpush(key, item)
        self.client.ltrim(key, 0, Config.MAX_HISTORY_ROUNDS - 1)
        self.client.expire(key, Config.CACHE_EXPIRE_SECONDS)
