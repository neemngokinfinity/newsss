# Rakazo — VPS Deployment Bundle

Safe-to-share deployment config for the Rakazo self-host stack
(https://github.com/elie222/rakazo). **No secrets included.**

## Contents
- `docker-compose.images.yml` — official published-image Compose stack (postgres, api, worker, web, supervisor, computer)
- `docker-compose.override.yml` — Tailscale/ts.net overrides (Vite allowedHosts, Better Auth origins)
- `install-images.sh` — official installer (downloads compose + generates `.env` with random secrets)
- `restrict-computer-egress.sh` — host firewall rules for restricted sandbox egress
- `.env.example` — template (copy to `.env`, installer fills secrets automatically)
- `OPS.md` — operations guide (start/stop/restart/logs, volumes, Tailscale)
- `ENV_KEYS.txt` — which keys exist; backup ENCRYPTION_KEY etc.

## Deploy on a new machine
```
mkdir -p /opt/rakazo && cd /opt/rakazo
# copy files from this repo here
bash install-images.sh
```

## ⚠️ Security notes
- Never commit the real `.env` (contains secrets).
- Back up `ENCRYPTION_KEY`, `BETTER_AUTH_SECRET`, Postgres passwords (`.env`).
- Keep Postgres internal; web/API bind loopback; expose only via HTTPS (e.g. Tailscale serve / reverse proxy).
- This bundle has no credentials — the Tailscale hostname in `docker-compose.override.yml` is deployment-specific; adjust for yours.
