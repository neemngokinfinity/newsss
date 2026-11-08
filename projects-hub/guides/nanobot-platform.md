# Nanobot Platform — project guide

Full Nanobot AI-platform web UI (login, chat, tools, managers, deploy, tests) targeting the Nanobot backend API, plus GitHub repo. Delivered in `nanobot-platform/` in this repo (repo root = original Nanobot source; `ui/` = the built UI).

## What's in the bundle
- `ui/index.html`, `ui/css/app.css`, `ui/js/api.js`, `ui/js/chat.js`, `ui/js/main.js`, `ui/js/manage.js`, `ui/js/ui.js`
- Backend API surface the UI targets:
  - MCP routes at `/api/mcpservers` (no trailing slash)
  - Tool toggle = `POST /api/tools/{server}/{tool}/toggle`
  - Provider config field is `baseURL` (masked via hasKey)
  - Logs endpoint returns `{"lines":[...]}`
  - Dashboard uses `/api/system/status` (cpu.load1, mem.total/used bytes, conversations)
  - Settings page = theme + showToolCalls only (no admin password change UI)
  - Agents CRUD at `/api/config/agents` (GET/POST/PUT/DELETE)
- API client sends `baseURL`/`apiKey` (not base_url/api_key); audit entries render as action/actor/ts.

## UI pages
- Login (API base URL + key)
- Chat
- Tools manager (toggle per server/tool)
- Agents manager (CRUD)
- Dashboard (system status)
- Settings (theme + showToolCalls)
- Deploy/tests sections

## Notes
- Built against the Nanobot backend API surface above — keep endpoint/field names in sync if the backend evolves.
- No secrets in the repo; keys are entered at login and stored client-side only.
