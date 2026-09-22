# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Анонимизирующий прокси: UUID / поле `УникальныйИдентификатор` больше не режутся паттернами CARD/INN/SNILS (ломало `get_nav_link` и цепочки `_objectRef`).

### Added
- Документация публикации HTTP-сервиса `mcp_APIBackend` на автономном сервере, запущенном из EDT (`infobases.yaml`, вложенный `http-services`, `mode: autouse`).
- `execute_code`: если база на БСП и включена блокировка работы с внешними ресурсами (база — копия), чёрный список опасных конструкций не применяется — разрешена запись/удаление данных, например для подготовки эталонной базы. Режим отражается в описании инструмента в `tools/list` и в поле ответа `dangerous_operations_allowed`.
- Роль расширения `mcp_ВыполнениеКодаИЗапросов`: доступ к `execute_code` и `execute_query` только при наличии этой роли и полных прав сеанса (иначе скрытие в `tools/list` и отказ в `tools/call`).
- Анонимизирующий HTTP MCP-прокси (`proxy/`): проброс запросов к `…/hs/mcp/` с сохранением `Authorization`, анонимизация ответов `tools/call` и детокенизация аргументов; token map изолирован по пользователю (хеш `Authorization`). Документация: запуск через `run_service.bat`, Windows-сервис (NSSM), публикация в IIS reverse proxy.
- Слияние с форком [RooLee10/1c-mcp-tools](https://github.com/RooLee10/1c-mcp-tools): инструмент работы с запросами и улучшенные описания метаданных для LLM.
- Инструменты из [ROCTUP/1c-mcp-toolkit](https://github.com/ROCTUP/1c-mcp-toolkit):
  - `execute_code` (`mcp_ИнструментВыполнениеКода`) — выполнение кода 1С на сервере с чёрным списком опасных конструкций.
  - `get_event_log` (`mcp_ИнструментЖурналРегистрации`) — чтение журнала регистрации с фильтрами и курсорной пагинацией.

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
  - Добавлено предупреждение о безопасности данных при работе с AI
