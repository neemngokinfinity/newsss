# TGWebDrive — Deployment Bundle

Self-hosted Telegram cloud drive (mirror of [Sam8r/TGWebDrive](https://github.com/Sam8r/TGWebDrive)), deployed on the nanobot VPS via Docker. This bundle is sanitized (no secrets — `.env`, SQLite DBs and backouts are excluded).

## Stack
- Docker image `tgwebdrive:latest` (node:24-bookworm, better-sqlite3 compiled in-image)
- Container `tgwebdrive`: no host port published; reachable only via Cloudflare quick tunnel (container `cf-tgwd`)
- SQLite data via bind mount `./data:/app/data` (DB + Telegram sessions + backups)
- `restart: unless-stopped` (no systemd on VPS)
- Healthcheck: `GET /api/health` every 30s

## Deploy on a fresh host
1. `cd tgwebdrive-deploy`
2. Create `.env` (`SECRET` for sessions; `API_PRESETS` for Telegram api_id/api_hash; `PUBLIC_URL` = tunnel URL)
3. `docker compose up -d --build`
4. Open Public URL → create admin → connect Telegram account (OTP/2FA in UI)
5. Optional: add API key via admin panel (`GET/POST /api/keys`)

## Quick tunnel caveat
`cloudflared tunnel --url` generates a random URL each restart. After restarting `cf-tgwd`:
```bash
docker logs cf-tgwd 2>&1 | grep trycloudflare
```
Update `PUBLIC_URL` in `.env`, then `docker compose up -d tgwebdrive`.

## REST API (header `X-API-Key: tdk_...`)
- `GET  /api/v1/folders`
- `GET  /api/v1/files?folder=<id>&limit=<n>`
- `POST /api/v1/files?folder=<id>` — raw body; headers `X-Filename`, `X-Filesize`, `X-Caption`, `X-Force-Document`
- `GET  /api/v1/files/:id/raw?dl=1` — stream/download (folder param required)
- `DELETE /api/v1/files?folder=<id>&ids=<id1,id2>` (folder param required)
- Admin: `/api/auth/*`, `/api/users`, `/api/keys`, `/api/accounts`, `/api/auth/tg/*`

Selftest: `docker exec tgwebdrive node data/selftest.cjs` (folders → upload → download byte-exact → delete).

## Backup
- `backup.sh`: SQLite live backup to `./data/backups/`, rotated (keep 14)
- Daily cron job `tgwebdrive-daily-backup` at 02:30 UTC
- Restore: place backup sqlite into `data/` and restart container (files themselves live in Telegram — only metadata/sessions are local)

## Files
- `Dockerfile` / `docker-compose.yml` — service definition (compose expects source tree at `../tgwebdrive`)
- `backup.sh` — backup + rotation
- `check-tg.js`, `data/selftest.cjs` — diagnostics / API selftest
- `DEPLOY-LOG.md` — full deployment history
