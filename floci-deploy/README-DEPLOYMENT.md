# Floci — Deployment Notes (VPS)

Deployed: 2026-11-06, VPS (2 CPU / 7.88 GiB).

## Current state

- Stack: `floci` + `floci-ui-probe` (sidecar), no official compose file changes
  except loopback bindings.
- Image: `floci/floci:2.4.0`.
- Data volume: `floci-data`.
- Endpoints: 4566 (API), 4500 (console), 6379, 6400, 7001, 8182 — all loopback.
- Auth: `test`/`test` (dummy).

## Quick commands

```bash
cd floci-deploy
docker compose up -d          # start
docker compose ps             # status
docker compose logs -f floci # follow logs
docker compose down           # stop (keeps volume)
```

## Safety rules

- Do not stop/modify existing services (rakazo, openwa, hermes, paperclip, …).
- Only bind ports to 127.0.0.1.
- Never commit `.env` or `data/` (real/audit data).
- If disk is tight: `docker image prune -a` (keep floci image), keep volume.

## Data

- S3/DynamoDB/etc. data lives in `floci-data` volume → restore via
  [BACKUP-RESTORE.md](BACKUP-RESTORE.md).
