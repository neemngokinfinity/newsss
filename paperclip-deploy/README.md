# Paperclip AI — Deployment Guide (VPS)

**Status: DEPLOYED & LIVE** (2026-11-06) — authenticated mode, public exposure,
external Postgres sidecar.

Paperclip is a self-hosted AI platform (board, agents, providers, secrets,
routines, governance). This bundle deploys the official image with a Postgres
sidecar — no `npx paperclipai onboard` shell flow required.

## Stack

| Service | Image | Host port | Notes |
|---|---|---|---|
| paperclip | ghcr.io/paperclipai/paperclip:latest | 127.0.0.1:3110 → 3100 | Main app (static UI + API) |
| paperclip-db | postgres:16.3-alpine | — (internal) | Data DB for the app |

- Deployment mode: `authenticated` + `public` (login required, explicit public URL).
- Persistence: `./data/docker-paperclip` (app state) + `./data/docker-paperclip-pg` (Postgres).
- `/tmp` inside the container is a tmpfs (512m) — required, because the app's
  tsx runtime choked on a full/limited `/tmp` (`ENOSPC`).

## Prerequisites

- Docker + Compose v2.
- A public URL — Cloudflare quick tunnel (`cloudflared tunnel --url http://127.0.0.1:3110`)
  or a fixed domain. Quick-tunnel URLs change on restart; update `.env` when it does.
- Two secrets (generate with `openssl rand -base64 48`).

## Deploy

```bash
# 1. environment
cp .env.example .env && chmod 600 .env
$EDITOR .env   # set PAPERCLIP_PUBLIC_URL, ALLOWED_HOSTNAMES, BETTER_AUTH_SECRET, signing secret

# 2. start
docker compose -f docker-compose.deploy.yml up -d

# 3. verify
docker compose -f docker-compose.deploy.yml ps   # both healthy
# health: 200 {"status":"ok","bootstrapStatus":"bootstrap_pending",...}
curl http://127.0.0.1:3110/api/health
```

## First admin (bootstrap)

The instance starts in `bootstrap_pending` state. A one-time `bootstrap_ceo`
invite is required to claim first admin. Two ways to create it:

### Option A — CLI (inside container, installs on demand)

```bash
docker exec paperclip npx -y paperclipai auth bootstrap-ceo
# prints: <PUBLIC_URL>/invite/<token>
```

### Option B — direct SQL (no image)

```bash
# token = "pcp_bootstrap_" + 48 hex chars (openssl rand -hex 24)
# hash  = sha256(token) in hex
TOKEN=$(openssl rand -hex 24)
TOKEN="pcp_bootstrap_$TOKEN"
HASH=$(printf %s "$TOKEN" | sha256sum | cut -d' ' -f1)

docker exec -i paperclip-db psql -U paperclip -d paperclip <<SQL
UPDATE invites SET revoked_at=now(), updated_at=now()
  WHERE invite_type='bootstrap_ceo' AND revoked_at IS NULL
    AND accepted_at IS NULL AND expires_at > now();
INSERT INTO invites (invite_type, token_hash, allowed_join_types, expires_at, invited_by_user_id)
VALUES ('bootstrap_ceo', '$HASH', 'human', now() + interval '72 hours', 'system');
SQL
# invite URL = <PUBLIC_URL>/invite/$TOKEN
```

Open the invite URL in a browser → sign up → claim first admin. The invite is
one-time and expires after 72h.

## Environment variables

| Variable | Required | Meaning |
|---|---|---|---|
| `PAPERCLIP_PUBLIC_URL` | yes | Public URL users visit (must match Host header) |
| `PAPERCLIP_ALLOWED_HOSTNAMES` | yes | Comma-separated allowed hostnames |
| `BETTER_AUTH_SECRET` | yes | Auth/session secret (≥32 random chars) |
| `PAPERCLIP_TOOL_ACTION_SIGNING_SECRET` | no | Signs agent tool actions |
| `PAPERCLIP_DEPLOYMENT_MODE` | fixed | `authenticated` |
| `PAPERCLIP_DEPLOYMENT_EXPOSURE` | fixed | `public` |
| `PAPERCLIP_HOME` | fixed | `/paperclip` |
| `DATABASE_URL` | fixed | point to `db:5432` (internal network) |

## Troubleshooting

- **Port 3100 taken** (e.g. Rakazo API on this VPS): change the host port in
  `ports:` (we use 3110) and point the tunnel at the new port.
- **`ENOSPC: mkdir /tmp/tsx-1000`**: the container's `/tmp` is too small —
  keep the `tmpfs: /tmp:rw,size=512m` entry.
- **Disk full**: the image is ~12.8G. Prune unused images/`docker builder prune -af`.
- **Tunnel URL changed**: update `PAPERCLIP_PUBLIC_URL` + `PAPERCLIP_ALLOWED_HOSTNAMES`
  in `.env`, then `docker compose -f docker-compose.deploy.yml up -d`. (Or keep the
  tunnel session pinned.)

## Backup

- `./data/docker-paperclip/` — app/instance state (config, secrets, backups).
- `./data/docker-paperclip-pg/` — Postgres data (stop DB for a consistent copy).
- `.env` — must be kept (contains auth secrets).
