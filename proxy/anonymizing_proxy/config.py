import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw.strip())


def _env_str(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    return default if raw is None else raw


@dataclass(frozen=True)
class Settings:
    upstream_url: str
    port: int
    timeout: float
    log_level: str

    anonymization_enabled: bool
    anonymization_tools: set[str]
    anonymization_radical_mode: bool
    anonymization_ner_enabled: bool
    anonymization_tokenmap_max: int


def _build_settings() -> Settings:
    upstream_url = _env_str("UPSTREAM_URL", "").strip()
    if not upstream_url:
        # We raise early so operator sees misconfiguration immediately.
        raise RuntimeError("UPSTREAM_URL env var is required (base URL of 1C HTTP MCP service).")

    tools_raw = _env_str("ANONYMIZATION_TOOLS", "execute_query,execute_code,get_event_log")
    tools = {t.strip() for t in tools_raw.split(",") if t.strip()}

    timeout = float(_env_str("TIMEOUT", "60").strip() or "60")

    return Settings(
        upstream_url=upstream_url,
        port=_env_int("PORT", 8080),
        timeout=timeout,
        log_level=_env_str("LOG_LEVEL", "INFO"),
        anonymization_enabled=_env_bool("ANONYMIZATION_ENABLED", True),
        anonymization_tools={t.lower() for t in tools},
        anonymization_radical_mode=_env_bool("ANONYMIZATION_RADICAL_MODE", False),
        anonymization_ner_enabled=_env_bool("ANONYMIZATION_NER_ENABLED", False),
        anonymization_tokenmap_max=_env_int("ANONYMIZATION_TOKENMAP_MAX", 10000),
    )


settings = _build_settings()

