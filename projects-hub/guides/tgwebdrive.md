# TGWebDrive — project guide (deploy + use)

Self-hosted Telegram cloud drive (based on Sam8r/TGWebDrive), deployed on the nanobot VPS via Docker. Full deploy bundle: `tgwebdrive-deploy/` in this repo.

## Stack
- Docker image `tgwebdrive:latest` (node:24-bookworm, better-sqlite3 compiled in-image)
- Container `tgwebdrive`: no host port published; reachable only via Cloudflare quick tunnel (sidecar `cf-tgwd`)
- SQLite data bind `./data:/app/data` (DB + Telegram sessions + backups)
- `restart: unless-stopped` (no systemd on VPS); healthcheck `GET /api/health`

## Deploy on a fresh host
1. `cd tgwebdrive-deploy`
2. Create `.env` from `.env.example` (mode 600): `SECRET` (openssl rand -hex 32), `API_PRESETS=api_id:api_hash`, `TUNNEL_URL=http://tgwebdrive:3001`, `PUBLIC_URL` filled after tunnel is up.
3. `docker compose up -d --build`
4. Open the tunnel URL → create admin → connect Telegram account (OTP/2FA in UI).
5. Optional: create API key in admin panel (shown once: `tdk_...`).

## Quick tunnel caveat
URL is random and changes each restart of `cf-tgwd`:
```bash
docker logs cf-tgwd 2>&1 | grep trycloudflare
```
Update `PUBLIC_URL` in `.env`, then `docker compose up -d tgwebdrive`.

## REST API (header `X-API-Key: tdk_...`)
- `GET /api/v1/folders`
- `GET /api/v1/files?folder=<id>&limit=<n>`
- `POST /api/v1/files?folder=<id>` — raw body; headers `X-Filename`, `X-Filesize`, `X-Caption`, `X-Force-Document`
- `GET /api/v1/files/:id/raw?dl=1` — download (folder param required)
- `DELETE /api/v1/files?folder=<id>&ids=<id1,id2>` (folder param required)
- Admin: `/api/auth/*`, `/api/users`, `/api/keys`, `/api/accounts`, `/api/auth/tg/*`

Selftest: `docker exec tgwebdrive node data/selftest.cjs` (folders → upload → download byte-exact → delete).

## Backup
- `backup.sh`: SQLite live backup to `./data/backups/`, rotated (keep 14)
- Daily cron `tgwebdrive-daily-backup` at 02:30 UTC
- Restore: stop app, replace `data/tgdrive.sqlite` with backup, start. (Files live in Telegram; only metadata/sessions are local.)

## Troubleshooting (top)
- Not reachable after tunnel restart → update `PUBLIC_URL`, recreate app.
- 401 Invalid API key → recreate key from dashboard (shown once).
- 400 Missing folder → raw/download/delete need `?folder=<id>`.
- OTP not arriving → check phone format (+code); 2FA prompt = Telegram password.

## Security checklist
- `.env` mode 600, never committed; api_hash only in `.env` + password manager.
- Keep bundle sanitized (no `.env`, no sqlite) when sharing.
- Copy backups off-box for real disaster recovery.
