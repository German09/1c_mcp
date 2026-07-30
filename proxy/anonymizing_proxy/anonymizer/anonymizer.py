from __future__ import annotations

import json
import re
from typing import Any

from .patterns import (
    FIO_RE,
    ORG_MARKERS_RE,
    INLINE_PATTERNS,
    key_hint_category,
    whole_value_category_by_heuristics,
    InlinePattern,
)
from .token_mapper import TokenMapper, TOKEN_RE


class Anonymizer:
    def __init__(
        self,
        token_mapper: TokenMapper,
        *,
        radical_mode: bool = False,
        ner_enabled: bool = False,
    ):
        self._token_mapper = token_mapper
        self._radical_mode = radical_mode
        self._ner_enabled = ner_enabled

        # Lazy import: SpaCy is optional.
        self._spacy = None
        if self._ner_enabled:
            try:
                import spacy  # type: ignore

                self._spacy = spacy
            except Exception:
                self._spacy = None

    def detokenize_in_text(self, session_id: str, text: str) -> str:
        return self._token_mapper.detokenize_in_text(session_id, text)

    def detokenize_in_obj(self, session_id: str, obj: Any) -> Any:
        return self._token_mapper.detokenize_in_obj(session_id, obj)

    def anonymize_json_text(self, session_id: str, text: str) -> str:
        try:
            parsed = json.loads(text)
        except Exception:
            return self.anonymize_plain_text(session_id, text)
        anon = self.anonymize_obj(session_id, parsed)
        return json.dumps(anon, ensure_ascii=False)

    def anonymize_plain_text(self, session_id: str, text: str) -> str:
        # Avoid double-processing already tokenized payloads.
        if TOKEN_RE.search(text) and TOKEN_RE.fullmatch(text.strip()):
            return text

        changed = False

        # Whole-value category heuristics first (for short "just value" strings).
        whole_cat = whole_value_category_by_heuristics(text)
        if whole_cat in {
            "ORG",
            "PER",
            "INN",
            "KPP_OR_BIK",
            "OGRN",
            "SNILS",
            "PHONE",
            "EMAIL",
        }:
            changed = True
            cat = self._map_whole_category(whole_cat)
            canonical = self._canonicalize_for_category(cat, text)
            return self._token_mapper.tokenize(session_id, cat, canonical)

        # Inline patterns.
        out = text
        for spec in INLINE_PATTERNS:
            def repl(m: re.Match[str], _spec: InlinePattern = spec) -> str:
                nonlocal changed
                changed = True
                val = m.group(0)
                canonical = _spec.canonicalize(val)
                return self._token_mapper.tokenize(session_id, _spec.category, canonical)

            out = spec.regex.sub(repl, out)

        if not changed and self._radical_mode and text.strip():
            return self._token_mapper.tokenize(session_id, "STR", text.strip())

        return out

    def anonymize_obj(self, session_id: str, obj: Any, key_hint: str | None = None) -> Any:
        if isinstance(obj, str):
            return self.anonymize_string(session_id, obj, key_hint=key_hint)
        if isinstance(obj, list):
            return [self.anonymize_obj(session_id, x) for x in obj]
        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for k, v in obj.items():
                next_hint = str(k) if k is not None else None
                if isinstance(v, (str, list, dict)):
                    out[k] = self.anonymize_obj(session_id, v, key_hint=next_hint)
                else:
                    out[k] = v
            return out
        return obj

    def anonymize_string(self, session_id: str, value: str, *, key_hint: str | None) -> str:
        if not value:
            return value

        # If it looks like JSON (execute_query wraps its result as JSON-string),
        # process it as JSON for better key-based heuristics.
        stripped = value.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            return self.anonymize_json_text(session_id, value)

        hint_cat = key_hint_category(key_hint or "")
        if hint_cat:
            if hint_cat == "ORG_OR_PER":
                # Special-case "Представление" - detect by ORG markers vs FIO.
                whole = whole_value_category_by_heuristics(value)
                if whole == "ORG":
                    return self._token_mapper.tokenize(session_id, "ORG", value.strip())
                if whole == "PER":
                    return self._token_mapper.tokenize(session_id, "PER", value.strip())
                # Fall through: if radical mode, hide as STR.
            else:
                canonical = self._canonicalize_for_category(hint_cat, value)
                if canonical:
                    return self._token_mapper.tokenize(session_id, hint_cat, canonical)

        # Try whole-value heuristics (for short values).
        whole_cat = whole_value_category_by_heuristics(value)
        if whole_cat:
            cat = self._map_whole_category(whole_cat)
            canonical = self._canonicalize_for_category(cat, value)
            if canonical:
                return self._token_mapper.tokenize(session_id, cat, canonical)

        # Inline patterns.
        return self.anonymize_plain_text(session_id, value)

    @staticmethod
    def _map_whole_category(whole_cat: str) -> str:
        if whole_cat == "KPP_OR_BIK":
            return "KPP"
        return whole_cat

    @staticmethod
    def _canonicalize_for_category(category: str, value: str) -> str:
        c = category.upper()
        if c in {"INN", "KPP", "OGRN", "SNILS", "BIK", "ACC", "CARD", "PHONE"}:
            digits = re.sub(r"\D+", "", value)
            if c == "PHONE":
                if digits.startswith("8") and len(digits) == 11:
                    digits = "7" + digits[1:]
            return digits
        if c == "EMAIL":
            return value.strip().lower()
        if c == "SWIFT":
            return value.strip().upper()
        if c == "IBAN":
            return value.strip().upper()
        if c in {"ORG", "PER", "STR"}:
            return value.strip()
        # Unknown: keep original.
        return value.strip()

