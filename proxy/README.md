# Anonymizing MCP Proxy (1C HTTP)

Этот каталог содержит Python-прокси, который:
1) принимает MCP запросы от AI-клиента к `…/hs/mcp/` (JSON-RPC via HTTP);
2) пробрасывает их в ваш HTTP-сервис 1С (с сохранением заголовков, включая `Authorization`);
3) анонимизирует `result.content[].text` в ответах `tools/call` (по env-настройкам);
4) детокенизирует аргументы запросов `tools/call` до отправки в 1С (in-memory token map по сессии).

## Запуск

1. Установите зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Настройте env:

```powershell
$env:UPSTREAM_URL = "https://pos5000.askona.ru/pos5000wa-/hs/mcp/"
$env:PORT = "8080"
$env:ANONYMIZATION_ENABLED = "true"
$env:ANONYMIZATION_TOOLS = "execute_query"
```

3. Запуск:

```powershell
cd proxy
python -m anonymizing_proxy
```

## Подключение клиента

Укажите URL прокси (локально):

```json
{
  "mcpServers": {
    "1c-server": {
      "url": "http://localhost:8080/",
      "headers": { "Authorization": "Basic <Base64>" }
    }
  }
}
```

## Env

- `UPSTREAM_URL` — базовый URL вашего HTTP-сервиса 1С (обязателен)
- `PORT` — порт прокси (default `8080`)
- `ANONYMIZATION_ENABLED` — включить/выключить анонимизацию (default `true`)
- `ANONYMIZATION_TOOLS` — whitelist через запятую (default `execute_query,execute_code`)
- `ANONYMIZATION_RADICAL_MODE` — токенизировать всё как `STR` (default `false`)
- `ANONYMIZATION_NER_ENABLED` — NER через SpaCy (default `false`, optional)
- `ANONYMIZATION_TOKENMAP_MAX` — лимит token map на сессию (default `10000`)
- `TIMEOUT` — timeout в секундах для upstream (default `60`)

## Несколько пользователей и изоляция токенов

Прокси можно использовать одновременно несколькими пользователями 1С. Маппинг токенов (`[ORG-00001]` ↔ реальное значение) **разделён по сессиям**.

Ключ сессии — SHA-256 от заголовка `Authorization` (сырой логин/пароль в памяти не хранится):

- разные `Authorization: Basic …` → независимые token map;
- один и тот же Basic Auth у нескольких клиентов → общий маппинг;
- запрос без `Authorization` → общий bucket `anonymous` (не рекомендуется).

Ограничения:

- маппинг только **в памяти** процесса прокси и сбрасывается при рестарте;
- на сессию действует лимит `ANONYMIZATION_TOKENMAP_MAX` (при превышении маппинг сессии очищается).

