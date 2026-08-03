# Anonymizing MCP Proxy (1C HTTP)

Этот каталог содержит Python-прокси, который:
1) принимает MCP-запросы от AI-клиента к `…/hs/mcp/` (JSON-RPC via HTTP);
2) пробрасывает их в ваш HTTP-сервис 1С (с сохранением заголовков, включая `Authorization`);
3) анонимизирует `result.content[].text` в ответах `tools/call` (по env-настройкам);
4) детокенизирует аргументы запросов `tools/call` до отправки в 1С (in-memory token map по сессии).

Схема:

```text
AI-клиент  →  (опционально IIS HTTPS)  →  прокси :8080  →  https://host/имя_публикации/hs/mcp/
```

## Запуск вручную

1. Установите зависимости **на этой машине** (не копируйте `.venv` с другого ПК):

```powershell
cd <путь>\proxy
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Создайте `.env` из примера и укажите upstream:

```powershell
copy env.example .env
# отредактируйте UPSTREAM_URL в .env
```

Пример `.env`:

```env
UPSTREAM_URL=https://host/имя_публикации/hs/mcp/
PORT=8080
ANONYMIZATION_ENABLED=true
ANONYMIZATION_TOOLS=execute_query
LOG_LEVEL=INFO
```

3. Запуск через батник (читает `.env`, пишет лог в `logs\service.log`):

```powershell
.\run_service.bat
```

Либо напрямую:

```powershell
$env:UPSTREAM_URL = "https://host/имя_публикации/hs/mcp/"
$env:PORT = "8080"
$env:ANONYMIZATION_ENABLED = "true"
.\.venv\Scripts\python.exe -m anonymizing_proxy
```

Проверка:

```powershell
Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing
```

Без `Authorization` ожидаемо **401** от 1С — значит проброс работает.

## Подключение клиента

Локально (напрямую к прокси):

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

Через IIS (HTTPS) — отдельный путь или отдельный сайт, см. [Публикация в IIS](#публикация-в-iis):

```json
{
  "mcpServers": {
    "1c-server": {
      "url": "https://host/mcp-proxy/",
      "headers": { "Authorization": "Basic <Base64>" }
    }
  }
}
```

## Env

- `UPSTREAM_URL` — базовый URL HTTP-сервиса 1С MCP (обязателен), например `https://host/имя_публикации/hs/mcp/`
- `PORT` — порт прокси (default `8080`)
- `ANONYMIZATION_ENABLED` — включить/выключить анонимизацию (default `true`)
- `ANONYMIZATION_TOOLS` — whitelist через запятую (default `execute_query,execute_code,get_event_log`)
- `ANONYMIZATION_RADICAL_MODE` — токенизировать всё как `STR` (default `false`)
- `ANONYMIZATION_NER_ENABLED` — NER через SpaCy (default `false`, optional)
- `ANONYMIZATION_TOKENMAP_MAX` — лимит token map на сессию (default `10000`)
- `TIMEOUT` — timeout в секундах для upstream (default `60`)
- `LOG_LEVEL` — уровень логов uvicorn (default `INFO`)

## Несколько пользователей и изоляция токенов

Прокси можно использовать одновременно несколькими пользователями 1С. Маппинг токенов (`[ORG-00001]` ↔ реальное значение) **разделён по сессиям**.

Ключ сессии — SHA-256 от заголовка `Authorization` (сырой логин/пароль в памяти не хранится):

- разные `Authorization: Basic …` → независимые token map;
- один и тот же Basic Auth у нескольких клиентов → общий маппинг;
- запрос без `Authorization` → общий bucket `anonymous` (не рекомендуется).

Ограничения:

- маппинг только **в памяти** процесса прокси и сбрасывается при рестарте;
- на сессию действует лимит `ANONYMIZATION_TOKENMAP_MAX` (при превышении маппинг сессии очищается).

### UUID и `_objectRef`

Строки вида UUID (`8-4-4-4-12`) и поле `УникальныйИдентификатор` **не анонимизируются**: иначе CARD/INN-паттерны портят GUID, и `get_nav_link` / параметры `execute_query` перестают находить объект. Для цепочек object ref в `ANONYMIZATION_TOOLS` должны быть и `execute_query`, и `get_nav_link` (и при необходимости `parse_nav_link`).

## Windows-сервис (NSSM)

На **каждой** машине нужны свои локальные пути: каталог `proxy`, `.venv`, Python.  
Служба должна запускать **`run_service.bat`**, а не `python -m …` напрямую.

### 1. Подготовка

```powershell
cd <путь>\proxy
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy env.example .env
# укажите UPSTREAM_URL в .env
```

### 2. Обязательная проверка через батник

До установки службы убедитесь, что ручной запуск успешен:

```powershell
.\run_service.bat
```

В консоли / `logs\service.log` не должно быть traceback. Оставьте процесс работающим и проверьте:

```powershell
Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing
```

Остановите батник (Ctrl+C). Если bat падает — **не ставьте службу**, сначала исправьте по логу.

Типичные ошибки в `logs\service.log`:

| Сообщение | Что сделать |
|---|---|
| `UPSTREAM_URL is not set` | Создать `.env` из `env.example` |
| `.venv not found` | Создать venv на **этой** машине |
| `No module named 'pydantic_core._pydantic_core'` | Пересоздать `.venv` локально (`Remove-Item .venv -Recurse`, затем снова `venv` + `pip install`) |
| `Address already in use` | Сменить `PORT` в `.env` или остановить другой процесс на порту |

### 3. Установка службы

PowerShell **от администратора**. Подставьте локальные пути:

```powershell
$nssm = "C:\Tools\nssm\win64\nssm.exe"   # путь к nssm.exe на этой машине
$dir  = "D:\proxy"                       # каталог proxy на этой машине

& $nssm install OnecMcpAnonProxy "$dir\run_service.bat"
& $nssm set OnecMcpAnonProxy AppDirectory $dir
& $nssm set OnecMcpAnonProxy DisplayName "1C MCP Anonymizing Proxy"
& $nssm set OnecMcpAnonProxy Description "Anonymizing reverse proxy for 1C MCP HTTP"
& $nssm set OnecMcpAnonProxy Start SERVICE_AUTO_START
& $nssm set OnecMcpAnonProxy AppStdout "$dir\logs\nssm-stdout.log"
& $nssm set OnecMcpAnonProxy AppStderr "$dir\logs\nssm-stderr.log"
& $nssm set OnecMcpAnonProxy AppRotateFiles 1
& $nssm set OnecMcpAnonProxy AppRotateBytes 10485760
& $nssm start OnecMcpAnonProxy
& $nssm status OnecMcpAnonProxy
```

`UPSTREAM_URL` и прочие переменные читаются из `proxy\.env` через `run_service.bat`.

Управление:

```powershell
nssm start OnecMcpAnonProxy
nssm stop OnecMcpAnonProxy
nssm restart OnecMcpAnonProxy
nssm status OnecMcpAnonProxy
```

### 4. Если служба не стартует

Сообщение Windows *«The service did not return an error»* почти всегда значит: NSSM запустился, а **Python-процесс сразу упал**.

1. Смотрите `logs\service.log` и `logs\nssm-stderr.log`.
2. Снова проверьте `.\run_service.bat` вручную.
3. Проверьте настройки NSSM:

```powershell
nssm get OnecMcpAnonProxy Application
nssm get OnecMcpAnonProxy AppDirectory
```

`Application` должен быть полным путём к `run_service.bat`, `AppDirectory` — каталог `proxy`.

Переустановка с нуля:

```powershell
nssm stop OnecMcpAnonProxy
nssm remove OnecMcpAnonProxy confirm
# затем снова шаги 2–3
```

## Публикация в IIS

IIS не запускает Python сам: он принимает HTTPS снаружи и проксирует на службу `http://127.0.0.1:8080` (reverse proxy).

### Предварительные условия

1. Служба `OnecMcpAnonProxy` запущена и отвечает на `http://127.0.0.1:8080/health`.
2. Установлены модули IIS:
   - [URL Rewrite](https://www.iis.net/downloads/microsoft/url-rewrite)
   - [Application Request Routing (ARR)](https://www.iis.net/downloads/microsoft/application-request-routing)
3. В IIS Manager → сервер → **Application Request Routing Cache** → **Server Proxy Settings** → включите **Enable proxy** → Apply.

### Вариант A: отдельный путь на существующем сайте (например `/mcp-proxy/`)

На сайте публикации (например `https://host/`) создайте **Application**:

- Alias: `mcp-proxy` (имя на ваш выбор)
- Physical path: пустая папка, например `C:\inetpub\mcp-proxy`

В этой папке `web.config` — пути в правиле **относительны приложению**, префикс `/mcp-proxy` IIS снимает сам:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="ReverseProxyToMcpAnonProxy" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:8080/{R:1}" />
        </rule>
      </rules>
    </rewrite>
    <security>
      <requestFiltering>
        <requestLimits maxAllowedContentLength="52428800" />
      </requestFiltering>
    </security>
  </system.webServer>
</configuration>
```

Клиент MCP:

```json
{
  "mcpServers": {
    "1c-server": {
      "url": "https://host/mcp-proxy/",
      "headers": {
        "Authorization": "Basic <Base64Строка>"
      }
    }
  }
}
```

Проверка:

```powershell
$headers = @{ Authorization = "Basic <Base64>" }
Invoke-WebRequest https://host/mcp-proxy/health -Headers $headers -UseBasicParsing
```

Если правило вешаете **на уровне сайта** (не Application), явно снимайте префикс:

```xml
<rule name="ReverseProxyToMcpAnonProxy" stopProcessing="true">
  <match url="^mcp-proxy/(.*)" />
  <action type="Rewrite" url="http://127.0.0.1:8080/{R:1}" />
</rule>
```

Иначе на backend уйдёт путь `/mcp-proxy/...`, и прокси/1С вернут 404.

### Вариант B: отдельный сайт в корне

Отдельный сайт/хост без path-prefix:

- Binding HTTPS, например `https://mcp-proxy.example.com/`
- Physical path: пустая папка, например `C:\inetpub\mcp-proxy`

`web.config` тот же, что у Application (match `(.*)`, rewrite на `http://127.0.0.1:8080/{R:1}`).

Клиент: `"url": "https://mcp-proxy.example.com/"`.

### Authentication на сайте/приложении прокси

Чтобы клиентский `Authorization: Basic …` доходил до Python и далее до 1С:

- в **Authentication** для этого сайта/приложения оставьте только **Anonymous Authentication** (Enabled);
- **Basic Authentication** и остальные методы — **Disabled**, иначе IIS перехватит Basic сам.

`UPSTREAM_URL` в `.env` сервиса по-прежнему указывает на публикацию 1С (`https://host/имя_публикации/hs/mcp/`), а не на URL IIS-прокси.

### Частые проблемы IIS

| Проблема | Что проверить |
|---|---|
| 502 Bad Gateway | Служба не запущена / не слушает `127.0.0.1:8080` |
| 401 на всём | Нет или неверный `Authorization` у клиента |
| 401 при верном Basic | IIS Authentication перехватывает Basic — выключить Basic Auth на приложении/сайте прокси |
| 404 на MCP при пути `/mcp-proxy/` | Префикс не снят: используйте Application или правило `^mcp-proxy/(.*)` → `8080/{R:1}` |
| Редирект POST→GET на 1С | Несовпадение регистра имени публикации в `UPSTREAM_URL` |
