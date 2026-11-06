# Obot — AI Governance Platform

Open-source platform for organizations to manage, secure, and govern their AI ecosystems. MCP/LLM gateways, hosted MCP servers, agent access control, and audit logs.

[Obot Platform](https://github.com/obot-platform/obot)

---

## 📦 Deploy (Docker Compose)

### 1. Clone + navigate
```bash
git clone https://github.com/neemngokinfinity/newsss
cd newsss/obot-deploy
```

### 2. Configure environment
```bash
cp .env.example .env
# (Optional) Edit .env for your settings — see notes below
```

**Key variables:**
| Variable | Default | Notes |
|---|---|---|
| `OBOT_SERVER_ENABLE_AUTHENTICATION` | `true` | Enable sign-in |
| `OBOT_BOOTSTRAP_TOKEN` | *(generated)* | First-login admin token — must be ≥6 chars. **Set a strong one if you plan external access** |
| `OBOT_SERVER_HOSTNAME` | *(empty)* | **Required for OAuth**: your public URL (e.g. `https://your-tunnel.trycloudflare.com`) |
| `OBOT_SERVER_PORT` | `8080` | Container-internal port |

> **⚠️ Security:** `OBOT_BOOTSTRAP_TOKEN` grants full admin access. For any public/remote access, replace the default with a long random string (e.g. `openssl rand -hex 32`).

### 3. Start
```bash
docker compose pull
docker compose up -d
```

### 4. Open the UI
```bash
open http://localhost:8080
```
Sign in with the `OBOT_BOOTSTRAP_TOKEN` value from your `.env`.

---

## ☁️ Expose via Cloudflare quick tunnel (phone/desktop access)

Quick tunnels regenerate their URL on restart — treat them as temporary.

1. **Get the URL** (run inside a persistent tmux session, e.g. `tmux new -s cf-obot`):
   ```bash
   /usr/local/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8100
   ```
   Copy the printed `https://...trycloudflare.com`.

2. **Tell Obot its public URL** (update `.env`):
   ```env
   OBOT_SERVER_HOSTNAME=https://your-new-url.trycloudflare.com
   ```
   Recreate:
   ```bash
   docker compose up -d
   ```

3. Access at `https://your-new-url.trycloudflare.com`.

> ⚠️ Quick-tunnel URLs change on every restart. For production use, create a **pre-created named Cloudflare Tunnel** (accountless tunnels have no uptime guarantee).

---

## 🔧 Management

| Task | Command |
|---|---|
| Check status | `docker compose ps` |
| View logs | `docker compose logs -f` |
| Restart | `docker compose restart` |
| Full restart | `docker compose up -d --force-recreate` |
| Stop | `docker compose down` |

**Data persistence:** All data is stored in the `obot-data` Docker volume. Keep it around across restarts (default compose behavior).

```bash
docker volume ls | grep obot-data
docker volume rm obot-deploy_obot-data   # ⚠️ destroys all Obot data
```

---

## 🛡️ Production checklist

- [ ] Set a strong `OBOT_BOOTSTRAP_TOKEN`
- [ ] Set `OBOT_SERVER_HOSTNAME` to a stable URL (or use a named Cloudflare tunnel)
- [ ] Configure an **auth provider** in the UI (Local provider works for evaluation; SSO/Okta for teams)
- [ ] Add a **model provider** (OpenAI/Anthropic key) if you plan to use the LLM Gateway
- [ ] Run `docker system df` occasionally to monitor image/build-cache disk usage
- [ ] For production: use external PostgreSQL + Kubernetes deployment per Obot docs

---

## 📚 Resources

- Docs: https://docs.obot.ai
- Repo: https://github.com/obot-platform/obot
- Docker image: ghcr.io/obot-platform/obot:latest
- Discord: https://discord.com/invite/9sSf4UyAMC

---

**Deployed by nanobot | Home repo: https://github.com/neemngokinfinity/newsss**
