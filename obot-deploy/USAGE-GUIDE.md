# Obot Usage Guide

Obot = **AI governance platform**. Use it to expose, control, and audit AI tools (MCP servers) and model access.

---

## 1️⃣ First login

1. Open the UI → sign in with `OBOT_BOOTSTRAP_TOKEN` from `.env`
2. You now have **Owner** role
3. Go to **Admin → Authentication** and set up an auth provider
   - **Local** — create users in-app (good for evaluation/personal use)
   - SSO/Okta/SCIM — for teams

## 2️⃣ Add a model provider (LLM Gateway)

Go to **Admin → Model Providers** → add **OpenAI** or **Anthropic**:

```bash
# Set in .env and restart (safer than typing into UI):
OBOT_SERVER_ENABLE_AUTHENTICATION=true
OPENAI_API_KEY=sk-...
```

Why? The API key lives on the server — your users never see it.

## 3️⃣ Expose APIs as MCP servers

**Option A — OpenAPI API → MCP server (recommended for your tools):**
- OpenAPI schema + one tool per API operation
- Hosted as a Docker container or Kubernetes workload
- Example: convert your Telegram/WhatsApp API into MCP tools

**Option B — MCP Catalog:**
- Browse & install public MCP servers (GitHub repo: obot-platform/mcp-catalog)
- Pin entries to catalog snapshots
- Scope credentials per user

## 4️⃣ Set egress / network policies

Restrict which domains hosted MCP tools can reach. Obot injects destination-specific secrets at the egress gateway.

## 5️⃣ Explore

- **MCP Tester** — try tools before exposing them
- **Audit logs** — every MCP request, model request, token usage, cost

---

## Quick commands

| Task | Command |
|---|---|
| Start | `docker compose up -d` |
| Logs | `docker compose logs -f` |
| Restart | `docker compose restart obot` |
| Volume backup | `docker run --rm -v obot-data:/data -v $(pwd):/backup alpine tar czf /backup/obot-backup.tar.gz -C /data .` |

---

**Deploy bundle:** newsss/obot-deploy/ | **Repo:** obot-platform/obot
