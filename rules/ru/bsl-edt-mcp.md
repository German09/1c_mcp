# BSL через EDT-MCP

При работе с `.bsl` прочитай [INDEX.md](INDEX.md), затем по ситуации:

- [bsl-coding-style.md](bsl-coding-style.md) — стиль и соглашения кода
- [bsl-do-not-use.md](bsl-do-not-use.md) — обход коллекций: цикл; не `[]` с числом; `Получить(0)` при затруднённом цикле
- [bsl-tab-alignment.md](bsl-tab-alignment.md) — выравнивание Tab в группах присваиваний
- [bsl-static-typing.md](bsl-static-typing.md) — `@strict-types` и документирующие комментарии
- [bsl-ssl.md](bsl-ssl.md) — паттерны БСП (проект на БСП)
- [edt-mcp-write-safety.md](edt-mcp-write-safety.md) — перед любой записью через `write_module_source`

**NEVER:** читать/править `.bsl` через Read/Write/StrReplace — только MCP EDT (`read_method_source`, `read_module_source`, `write_module_source`).
