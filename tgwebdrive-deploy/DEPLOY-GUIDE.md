# TGWebDrive — Master Deploy Guideline

Complete step-by-step guide to deploy TGWebDrive on a **fresh VPS** (or re-deploy anywhere). No secrets in this file — everything is a template.

---

## 0. What you need

- A Linux VPS (tested: Debian/Ubuntu, 2 CPU / 4GB+ RAM / 10GB+ disk, root access)
- Docker + Docker Compose (installed below)
- A Telegram account (for login) + Telegram app credentials (api_id / api_hash)

## 1. Get Telegram app credentials (one time)

1. Open https://my.telegram.org → log in with your Telegram account
2. Go to **API development tools** → **Create application**
3. Title: anything (e.g. "My Cloud DriveWeb"), Short name: alphanumeric 5–32 chars
4. Copy **api_id** (number) and **api_hash** (string)
5. ⚠️ Keep api_hash private. Store it in your password manager too.

## 2. Install Docker + Compose on the fresh VPS

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker        # if systemd exists
docker --version && docker compose version
```

No systemd? Docker still runs (restart=unless-stopped handles auto-start).

## 3. Get the files

```bash
# 3a. TGWebDrive source code
git clone https://github.com/Sam8r/TGWebDrive tgwebdrive

# 3b. This deploy bundle (from GitHub)
git clone https://github.com/neemngokinfinity/newsss.git tmp-newsss
cp -r tmp-newsss/tgwebdrive-deploy ./tgwebdrive-deploy
rm -rf tmp-newsss

cd tgwebdrive-deploy
```

Layout expected by compose: source at `../tgwebdrive` (sibling of `tgwebdrive-deploy`).

## 4. Create `.env` (secrets live here — never commit)

```bash
cp .env.example .env
nano .env
```

Template:

```bash
PORT=3001
HOST=127.0.0.1
# Generate with: openssl rand -hex 32
SECRET=REPLACE_WITH_LONG_RANDOM_HEX
# After tunnel is up, fill the real public URL (step 6)
PUBLIC_URL=https://your-tunnel-url.trycloudflare.com
# Telegram app credentials from step 1  (format: api_id:api_hash)
API_PRESETS=12345678:abcdef0123456789abcdef0123456789
# Internal service URL for the tunnel container
TUNNEL_URL=http://tgwebdrive:3001
```

Permissions: `chmod 600 .env`.

## 5. Build and start

```bash
docker compose up -d --build
docker ps
# Expect: tgwebdrive (healthy) + cf-tgwd (tunnel)
```

Healthcheck runs `GET /api/health` — wait until status shows `(healthy)`.

## 6. Tunnel URL (Cloudflare quick tunnel)

The tunnel URL is **random and changes on every restart** of `cf-tgwd`:

```bash
docker logs cf-tgwd 2>&1 | grep trycloudflare
# → https://random-words.trycloudflare.com
```

Then update `.env` → `PUBLIC_URL=` with that URL and restart the app:

```bash
docker compose up -d tgwebdrive
```

💡 Every future restart of `cf-tgwd` → re-run the grep + update PUBLIC_URL.

## 7. Create admin account

- Open the tunnel URL in a browser
- First visit shows the admin creation page → create admin (email + password)
- Log in (email + password)

## 8. Connect Telegram account

In the dashboard:
1. Go to Telegram settings / account connect
2. Enter phone number → Telegram sends OTP
3. Enter OTP (and 2FA password if your account has one)
4. On success you'll see "Saved Messages" folder

## 9. Create an API key (for automation)

- Dashboard → API keys → Create
- Choose the bound Telegram account
- Copy the key (shown once: `tdk_...`)
- Use it in the `X-API-Key` header for the REST API

## 10. Verify with selftest

```bash
docker exec tgwebdrive node data/selftest.cjs
# Expect: SELFTEST: ALL PASS (folders → upload → download → delete)
```

## 11. Backup (must-do)

- Test one backup:
  ```bash
  bash backup.sh
  ```
- Schedule daily (cron on the host, 02:30 UTC):
  ```bash
  crontab -e
  # add:
  30 2 * * * cd /path/to/tgwebdrive-deploy && bash backup.sh >> data/backups/cron.log 2>&1
  ```
- Backups land in `data/backups/tgdrive-YYYYMMDD-HHMMSS.sqlite`, kept 14 days
- Files themselves live in Telegram — only metadata/sessions are local

### Restore
- Stop app: `docker compose stop tgwebdrive`
- Replace `data/tgdrive.sqlite` with a backup
- Start: `docker compose start tgwebdrive`

---

## REST API cheat-sheet

Header: `X-API-Key: tdk_...`

| Purpose | Method + path |
|---|---|
| List folders | `GET /api/v1/folders` |
| List files | `GET /api/v1/files?folder=<id>&limit=60` |
| Upload | `POST /api/v1/files?folder=<id>` — raw body; headers `X-Filename`, `X-Filesize`, `X-Caption`, `X-Force-Document` |
| Download | `GET /api/v1/files/:id/raw?folder=<id>&dl=1` |
| Delete | `DELETE /api/v1/files?folder=<id>&ids=<id1,id2>` |

Admin (web session): `/api/auth/*`, `/api/users`, `/api/keys`, `/api/accounts`, `/api/auth/tg/*`

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| App not reachable after tunnel restart | Update `PUBLIC_URL` in `.env` → `docker compose up -d tgwebdrive` |
| 401 "Invalid API key" | Key shown once — recreate from dashboard if lost |
| 400 "Missing folder" | Raw/download/delete endpoints need `?folder=<id>` |
| Folder not found | Use a folder id from `GET /api/v1/folders` |
| OTP not arriving | Check phone number format (international +code) / resend |
| 2FA prompt | Your Telegram password (not OTP) |
| `docker compose up` fails on build | Host needs internet to pull images; increase RAM/disk |
| Container unhealthy | `docker logs tgwebdrive --tail 100` |

---

## Security checklist

- [ ] `.env` is `chmod 600`, never committed to git
- [ ] api_hash only in `.env` + your password manager
- [ ] API keys are scoped to an account; rotate if leaked (dashboard delete → recreate)
- [ ] Keep the deployment bundle sanitized (no `.env`, no sqlite) when sharing publicly
- [ ] Backups are on the same VPS — for disaster recovery, copy them off-box
