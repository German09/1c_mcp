from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class InlinePattern:
    category: str
    regex: re.Pattern[str]
    canonicalize: Callable[[str], str]

    def token_if_match(self, token_mapper, session_id: str, text: str, value: str) -> str:
        canonical = self.canonicalize(value)
        return token_mapper.tokenize(session_id, self.category, canonical)


def _digits_only(s: str) -> str:
    return re.sub(r"\D+", "", s)


# Standard UUID (8-4-4-4-12). 1C object refs use this form in MCP payloads.
UUID_RE = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)


def looks_like_uuid(value: str) -> bool:
    """True if the whole string is a UUID (optionally braced)."""
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}") and len(stripped) > 2:
        stripped = stripped[1:-1].strip()
    return bool(UUID_RE.fullmatch(stripped))


def is_identity_key(key: str | None) -> bool:
    """Keys whose values must not be touched by PII patterns (break get_nav_link)."""
    if not key:
        return False
    k = key.lower().replace("_", "")
    return k in {
        "уникальныйидентификатор",
        "uuid",
        "guid",
        "uniqueid",
        "uniqueidentifier",
    }


def canonical_inn(s: str) -> str:
    return _digits_only(s)


def canonical_phone(s: str) -> str:
    digits = _digits_only(s)
    # Normalize RU: allow +7 or 8; keep leading 7
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits


def canonical_email(s: str) -> str:
    return s.strip().lower()


def canonical_swift(s: str) -> str:
    return s.strip().upper()


INLINE_PATTERNS: list[InlinePattern] = [
    InlinePattern(
        category="INN",
        regex=re.compile(r"(?<!\d)(\d{10}|\d{12})(?!\d)"),
        canonicalize=canonical_inn,
    ),
    InlinePattern(
        category="KPP",
        regex=re.compile(r"(?<!\d)\d{9}(?!\d)"),
        canonicalize=_digits_only,
    ),
    InlinePattern(
        category="OGRN",
        regex=re.compile(r"(?<!\d)\d{13}(?!\d)"),
        canonicalize=_digits_only,
    ),
    InlinePattern(
        category="SNILS",
        # Accept: 123-456-789 00 / 12345678900
        regex=re.compile(r"(?<!\d)\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}(?!\d)"),
        canonicalize=_digits_only,
    ),
    InlinePattern(
        category="PHONE",
        regex=re.compile(
            r"(?<!\d)(?:\+7|8)\s*\(?\d{3}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)"
        ),
        canonicalize=canonical_phone,
    ),
    InlinePattern(
        category="EMAIL",
        regex=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        canonicalize=canonical_email,
    ),
    InlinePattern(
        category="BIK",
        regex=re.compile(r"(?<!\d)\d{9}(?!\d)"),
        canonicalize=_digits_only,
    ),
    InlinePattern(
        category="ACC",
        regex=re.compile(r"(?<!\d)\d{20}(?!\d)"),
        canonicalize=_digits_only,
    ),
    InlinePattern(
        category="SWIFT",
        regex=re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{4}[A-Za-z]{2}[A-Za-z0-9]{2}(?:[A-Za-z0-9]{3})?(?![A-Za-z0-9])"),
        canonicalize=canonical_swift,
    ),
    InlinePattern(
        category="IBAN",
        regex=re.compile(r"\bRU\d{2}[0-9A-Z]{11,30}\b", re.IGNORECASE),
        canonicalize=lambda s: s.strip().upper(),
    ),
    InlinePattern(
        category="CARD",
        # digits-only tokenization might be too wide; keep it conservative by requiring 13-19 digits with separators
        regex=re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
        canonicalize=lambda s: _digits_only(s),
    ),
]


ORG_MARKERS_RE = re.compile(r"(?i)\b(ООО|АО|ПАО|ЗАО|ИП)\b")


FIO_RE = re.compile(
    r"^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?$"
)


def key_hint_category(key: str) -> str | None:
    k = key.lower()
    if "инн" in k:
        return "INN"
    if "кпп" in k:
        return "KPP"
    if "огрн" in k:
        return "OGRN"
    if "снилс" in k:
        return "SNILS"
    if "тел" in k or "phone" in k:
        return "PHONE"
    if "email" in k or "почт" in k:
        return "EMAIL"
    if "бик" in k:
        return "BIK"
    if "счет" in k or "acc" in k or "расчет" in k:
        return "ACC"
    if "свифт" in k or "swift" in k:
        return "SWIFT"
    if "iban" in k:
        return "IBAN"
    if "карта" in k or "pan" in k:
        return "CARD"
    if "представлен" in k:
        return "ORG_OR_PER"  # special-case in anonymizer
    return None


def whole_value_category_by_heuristics(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None

    # UUID must not be classified as INN/SNILS/etc. by digit-length heuristics.
    if looks_like_uuid(stripped):
        return None

    if ORG_MARKERS_RE.search(stripped):
        return "ORG"
    if FIO_RE.match(stripped):
        return "PER"

    # numeric patterns full-match fallback (after normalization)
    digits = _digits_only(stripped)
    if len(digits) == 10 or len(digits) == 12:
        return "INN"
    if len(digits) == 9:
        return "KPP_OR_BIK"
    if len(digits) == 13:
        return "OGRN"
    if len(digits) == 11:
        return "SNILS"
    if len(digits) == 11 and (digits.startswith("7") or digits.startswith("8")):
        return "PHONE"
    if "@" in stripped:
        return "EMAIL"

    return None

