# Nanobot Platform 🐈

A self-hosted AI chat and management platform. It combines a chat UI with
tool use (MCP servers), provider management, agents, files, and an audit trail
— all behind a small FastAPI control plane with a single static frontend.

## Features

- **Chat** with live SSE streaming, markdown rendering, and tool-call display
- **Agents** — Markdown-defined personas (`agents/*.md`), CRUD from the UI
- **LLM providers** — OpenAI-compatible chat completions, Responses, and
  generic OpenResponses dialects; API keys are masked and never logged
- **MCP servers** — manage HTTP JSON-RPC MCP servers, discover tools, and
  enable/disable them individually
- **Files** — upload/download storage referenced by agents
- **Conversations** — persisted history with delete
- **Observability** — system status, logs viewer, audit trail
- **Auth** — JWT bearer + cookie sessions, admin bootstrap from env

## Quick start (Docker)

```bash
docker compose up -d --build
```

Then open http://localhost:8000. On first start an admin user is created from
`NANOBOT_ADMIN_USER` (default `admin`) and `NANOBOT_ADMIN_PASSWORD`; if the
password env is not set, a random one is written to `data/admin-password.txt`.

## Run without Docker

Python 3.12+ (other 3.x should work). The project vendors its dependencies in
`deps/` so it runs even without a working pip/venv (e.g. Debian with PEP 668):

```bash
# With pip available:
pip install -r requirements.txt

# Or use the vendored deps directly:
export PYTHONPATH=$PWD/deps:$PWD

NANOBOT_ADMIN_USER=admin NANOBOT_ADMIN_PASSWORD=secret \
  python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --ws none
```

Data lives in `data/` (config, agents, uploads, logs, sqlite db). Point
`NANOBOT_PLATFORM_DATA` elsewhere to relocate it.

## Configuration

`data/config/nanobot.yaml` mirrors the upstream nanobot format:

```yaml
llmProviders:
  openai:
    dialect: openai-chat          # openai-chat | openai-responses | generic-openresponses
    baseURL: https://api.openai.com/v1
    apiKey: ${OPENAI_API_KEY}     # env reference or literal
    model: gpt-4o-mini
mcpServers:
  my-server:
    transport: http                # only http JSON-RPC is supported
    url: http://host:port/mcp
    headers: {}
```

Agents are markdown files in `data/config/agents/` (frontmatter: `name`,
`description`, `provider`, `model`, `temperature`, `mcpServers`). A default
`main` agent is created on first start.

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` · `/api/auth/logout` | sessions |
| GET | `/api/auth/me`, `/api/version`, `/api/system/status` | info |
| GET/POST/PUT/DELETE | `/api/providers[/{name}][/test]` | LLM providers |
| GET/POST/PUT/DELETE | `/api/mcpservers[/{name}][/test]` | MCP servers |
| GET/POST/PUT/DELETE | `/api/config/agents[/{name}]` | agents |
| GET | `/api/tools` · POST `/api/tools/{server}/{tool}/toggle` | tool control |
| POST | `/api/chat` (SSE: `meta`, `delta`, `tool_start`, `tool_end`, `done`) | chat |
| GET/POST/DELETE | `/api/conversations[/{id}[/messages]]` | history |
| GET/POST/DELETE | `/api/files[/{name}]` | file storage |
| GET | `/api/logs`, `/api/audit` | observability |
| GET/PUT | `/api/settings` | theme / tool-call display |

## Deployment

- **Docker**: `docker-compose.yml`
- **systemd**: `deploy/nanobot-platform.service` (run as user `nanobot`, port 8000 localhost)
- **nginx**: `deploy/nginx.conf` (SSE-safe proxy, 50 MB uploads)

## Tests

```bash
PYTHONPATH=$PWD/deps:$PWD python3 -m pytest tests/ -q
```

## License & attribution

This project is a fork/companion control plane built for the open-source
**nanobot** engine by the obot-platform team. The upstream engine
(Go, Apache-2.0) is not included; this repository is an independent Python
implementation of the platform layer, and it reuses the upstream *configuration
format* (`nanobot.yaml`, `agents/*.md`) and *naming conventions* with
attribution.

- Upstream: https://github.com/obot-platform/nanobot (v0.0.92, Apache-2.0)
- This project: Apache License 2.0 (see LICENSE), with NOTICE attributing the upstream project.
