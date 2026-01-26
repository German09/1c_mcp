# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

## [1.0.6] - 2026-01-27

### Added
- Инструмент работы с запросами (`mcp_ИнструментРаботаСЗапросами`):
  - `execute_query`: Выполнение произвольных запросов 1С с поддержкой параметров и пагинации.
  - `validate_query`: Проверка синтаксиса запросов без выполнения.
  - `parse_nav_link` / `get_nav_link`: Конвертация навигационных ссылок в описания объектов и обратно.

### Changed
- Инструмент данных о конфигурации (`mcp_ИнструментДанныеОКонфигурации`):
  - Расширены и уточнены описания инструментов (`list_metadata_objects`, `get_metadata_structure`) для LLM.
  - Добавлены примеры использования, списки допустимых типов метаданных и рекомендации по цепочкам вызовов (Best Practices).
  - Реорганизация документации: оригинальный README перенесён в `ORIGINAL_README.md`
  - Новый README с описанием отличий форка и примерами использования
  - Добавлено предупреждение о безопасности данных при работе с AI
