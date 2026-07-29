# Команда добавления MCP-сервера для claude-code через HTTP-транспорт.
# Аутентификация — Basic Auth в заголовке Authorization.
#
# Base64Строка получается в 1С:
#   ПолучитьBase64СтрокуИзДвоичныхДанных(
#       ПолучитьДвоичныеДанныеИзСтроки("" + Пользователь + ":" + Пароль))
#
# Scope (область хранения):
#   По умолчанию сервер пишется в local scope (~/.claude.json),
#   доступен только вам и только в текущем проекте, в git не попадает.
#   Для командной работы используйте --scope project — тогда сервер
#   будет записан в .mcp.json в корне проекта (см. mcp.json рядом).

# Local scope (по умолчанию, только для вас):
claude mcp add --transport http 1c-md \
  --header "Authorization: Basic <Base64Строка>" \
  https://host/имя_публикации/hs/mcp/

# Project scope (запись в .mcp.json, для шаринга через git):
# claude mcp add --transport http --scope project 1c-md \
#   --header "Authorization: Basic <Base64Строка>" \
#   https://host/имя_публикации/hs/mcp/
