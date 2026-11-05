# OpenWA — Second Instance Deployment Bundle (VPS)

Safe, secret-free deployment config for an **isolated second OpenWA instance**
on the same VPS that already runs the Hermes-agent OpenWA stack.

## Why a second instance
The VPS already runs OpenWA (`openwa-api`, port 2785, volume `openwa_openwa-data`)
as part of the Hermes agent stack — it must not be touched. This bundle deploys a
separate OpenWA with its own container, volume, network, and port (2786).

## Files
- `docker-compose.second.yml` — isolated compose (SQLite, local storage, dashboard on 2785-in-container)
- `.env.example` — template: API_MASTER_KEY + API_KEY_PEPPER (secrets NEVER committed)
- `OPS.md` — commands and status

## Deploy
```
cd openwa-deploy
cp .env.example .env   # then fill secrets: openssl rand -hex 24
docker compose -f docker-compose.second.yml --project-name openwa2 up -d
```
Dashboard/API: http://127.0.0.1:2786 (loopback). Put TLS in front to expose.

## Upstream
Official project: https://github.com/rmyndharis/OpenWA (MIT, 16k+ stars)
Docs: https://openwa.dev
