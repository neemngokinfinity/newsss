# VoiceStudio — deploy guide (VPS / Docker / Cloudflare quick tunnel)

## 1. Prerequisites

- Docker + Compose on the host.
- A writable project dir, e.g. `voicestudio-deploy/` containing the files from
  this bundle.

## 2. Environment

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env`:

- `OMNIVOICE_API_KEY` — required, set it to a strong random value
  (e.g. `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`).
  It is the admin gate; the UI exchanges it for a short-lived session key.
- `OMNIVOICE_DATA_DIR=/app/omnivoice_data` — must match the compose volume.
- `OMNIVOICE_ANALYTICS_DISABLED=1` — analytics off.
- `OMNIVOICE_ALLOWED_HOSTS` / `OMNIVOICE_ALLOWED_ORIGINS` — set AFTER the tunnel
  is up (step 4). Empty until then is fine for local bring-up.

## 3. Start the studio

```bash
docker compose up -d omnivoice-studio
```

- First `docker compose up` pulls the image (~4.3 GB layers).
- First-run migrations run automatically; `GET /health` returns `503` while
  initializing and `200` when ready.
- Model weights are NOT auto-downloaded: the OmniVoice model licence must be
  accepted in the UI before the first engine download (deliberate policy).

Check readiness:

```bash
docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' omnivoice-studio
```

## 4. Start the Cloudflare quick tunnel

```bash
docker compose up -d cf-voicestudio
```

It waits for `omnivoice-studio` health, then prints the tunnel URL. Get it:

```bash
docker logs cf-voicestudio 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1
```

> Cloudflare quick tunnels are account-less: the URL CHANGES on every tunnel
> restart — see step 5 on how to re-apply it. The app is reachable only via the
> tunnel; no host port is published.

## 5. When the tunnel URL changes

1. `docker logs cf-voicestudio 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1`
2. Extract the hostname (drop `https://` and the path).
3. Update `.env`:
   - `OMNIVOICE_ALLOWED_HOSTS=<hostname>`
   - `OMNIVOICE_ALLOWED_ORIGINS=https://<hostname>`
   (Also update any UI config that hard-codes the old URL.)
4. Recreate the studio to pick up the new env:
   ```bash
   docker compose up -d omnivoice-studio
   ```
5. Verify: open `https://<hostname>` in a browser; the VoiceStudio login page
   should render (HTTP 200), not a host/origin rejection.

## 6. Verify

- `docker compose ps` — both containers `Up`, studio `healthy`.
- Browser/curl `https://<hostname>/` → 200 + UI.
- Model install: inside the UI, accept the OmniVoice licence before installing
  any engine (never auto-download by policy).

## 7. Backups

`./data` holds the DB and model/HF cache. Back up the whole `data/` directory
for a full restore.
