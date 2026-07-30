from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


TOKEN_RE = re.compile(r"\[(?P<cat>[A-Z]{2,})-(?P<num>\d{5})]")


def session_key_from_authorization(authorization_header: str | None) -> str:
    if not authorization_header:
        return "anonymous"
    # Don’t store raw auth; hash it.
    return hashlib.sha256(authorization_header.encode("utf-8", errors="ignore")).hexdigest()


@dataclass
class SessionTokens:
    counters: dict[str, int] = field(default_factory=dict)
    value_to_token: dict[str, dict[str, str]] = field(default_factory=dict)  # cat -> canonical -> token
    token_to_value: dict[str, str] = field(default_factory=dict)  # token -> canonical value

    def total_tokens(self) -> int:
        return len(self.token_to_value)


class TokenMapper:
    """
    In-memory token <-> value mapping per session.

    Needed for:
    - anonymize: create tokens for detected PII
    - detokenize: replace tokens back to original values inside the next requests
    """

    def __init__(self, tokenmap_max: int = 10000):
        self._tokenmap_max = int(tokenmap_max)
        self._sessions: dict[str, SessionTokens] = {}

    def _get_session(self, session_id: str) -> SessionTokens:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionTokens()
        return self._sessions[session_id]

    @staticmethod
    def make_token(category: str, idx: int) -> str:
        return f"[{category}-{idx:05d}]"

    def tokenize(self, session_id: str, category: str, canonical_value: str) -> str:
        session = self._get_session(session_id)

        category = category.upper()
        canonical_value = canonical_value.strip()
        if not canonical_value:
            # Fallback: if value is empty, don’t tokenize.
            return ""

        if category not in session.value_to_token:
            session.value_to_token[category] = {}

        existing = session.value_to_token[category].get(canonical_value)
        if existing:
            return existing

        # Soft cap: clear mapping for the session if it explodes.
        if session.total_tokens() >= self._tokenmap_max:
            session.counters.clear()
            session.value_to_token.clear()
            session.token_to_value.clear()

        idx = session.counters.get(category, 0) + 1
        session.counters[category] = idx
        token = self.make_token(category, idx)

        session.value_to_token[category][canonical_value] = token
        session.token_to_value[token] = canonical_value
        return token

    def detokenize_in_text(self, session_id: str, text: str) -> str:
        session = self._get_session(session_id)

        def repl(match: re.Match[str]) -> str:
            token = match.group(0)
            return session.token_to_value.get(token, token)

        return TOKEN_RE.sub(repl, text)

    def detokenize_in_obj(self, session_id: str, obj: Any) -> Any:
        if isinstance(obj, str):
            if "[" in obj and "]" in obj:
                return self.detokenize_in_text(session_id, obj)
            return obj
        if isinstance(obj, list):
            return [self.detokenize_in_obj(session_id, x) for x in obj]
        if isinstance(obj, dict):
            return {k: self.detokenize_in_obj(session_id, v) for k, v in obj.items()}
        return obj

