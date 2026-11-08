# Obot — project guide (AI governance platform)

Open-source platform (obot-platform/obot) to manage/secure AI ecosystems: MCP/LLM gateways, hosted MCP servers, agent access control, audit logs. Deployed on the nanobot VPS; full bundle in `obot-deploy/` (README.md + USAGE-GUIDE.md + .env.example + docker-compose.yml).

## Deploy (Docker Compose)
1. Clone repo, `cd obot-deploy`.
2. `cp .env.example .env` — key vars:
   - `OBOT_SERVER_ENABLE_AUTHENTICATION=true` (sign-in enabled)
   - `OBOT_BOOTSTRAP_TOKEN` — first-login admin token, must be ≥6 chars; set a LONG random string (`openssl rand -hex 32`) if exposing externally (it grants full admin)
   - `OBOT_SERVER_HOSTNAME` — public URL, required for OAuth
   - `OBOT_SERVER_PORT=8080` (container-internal)
3. `docker compose pull && docker compose up -d`.
4. Open UI at `http://localhost:8080`, sign in with bootstrap token → Owner role.

## Public access (Cloudflare quick tunnel)
- Tunnel URL changes on every restart — treat as temporary.
- Run `cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8100` in tmux (`tmux new -s cf-obot`).
- Update `.env` `OBOT_SERVER_HOSTNAME=https://<new-url>.trycloudflare.com`, then `docker compose up -d` to recreate.
- For stable access, use a pre-created named Cloudflare Tunnel.

## Post-deploy setup
- **Authentication**: Admin → Authentication → set up provider. Local provider = in-app users (good for eval/personal); SSO/Okta for teams.
- **Model provider** (LLM Gateway): Admin → Model Providers → add OpenAI/Anthropic. Key lives on server; users never see it.
- **Expose APIs as MCP servers**: Option A — OpenAPI schema → MCP (recommended; one tool per API op; e.g. convert Telegram/WhatsApp API into MCP tools). Option B — MCP Catalog (browse/install public MCP servers, e.g. obot-platform/mcp-catalog).
- **Egress/network policies**: restrict which domains hosted MCP tools can reach; destination-specific secrets injected at egress gateway.
- Explore: MCP Tester (try tools before exposing), Audit logs (every MCP/model request, token usage, cost).

## Management
- Status `docker compose ps`; logs `docker compose logs -f`; restart `docker compose restart obot`; recreate `docker compose up -d --force-recreate`; stop `docker compose down`.
- Data persists in Docker volume `obot-data` (keep across restarts). Backup: `docker run --rm -v obot-data:/data -v $(pwd):/backup alpine tar czf /backup/obot-backup.tar.gz -C /data .`.

## Production checklist
- Strong `OBOT_BOOTSTRAP_TOKEN`, stable `OBOT_SERVER_HOSTNAME` (named tunnel), auth provider configured, model provider added for LLM Gateway, monitor disk (`docker system df`); for production Obot docs suggest external PostgreSQL + Kubernetes.

## Notes (VPS instance)
- Owner account: bharat.us157@gmail.com (sign-in completes owner setup).
- Docker socket is mounted so hosted MCP servers run as sibling containers (dev/eval/trusted single-tenant only).
- Bundle: https://github.com/neemngokinfinity/newsss/tree/main/obot-deploy
