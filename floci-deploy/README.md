# Floci — Local AWS Emulator Deployment

**Status: DEPLOYED & TESTED** (2026-11-06) — Floci 2.4.0, image `floci/floci:2.4.0`.

Floci emulates AWS services locally for development/testing (S3, DynamoDB, SQS,
Lambda via real Docker, RDS/ElastiCache/Neptune proxies, and more). This bundle
documents the VPS deployment. Real AWS credentials are NEVER used — only dummy
`test`/`test` creds.

## Quick start

```bash
cp .env.example .env 2>/dev/null; chmod 600 .env   # or create .env per CONFIGURATION.md
docker compose up -d
docker inspect floci --format '{{.State.Health.Status}}'   # → healthy
docker logs --tail 20 floci                                # → "=== AWS Local Emulator Ready ==="
```

Endpoints (all loopback):

| Host port | Purpose |
|---|---|---|
| 4566 | AWS API (primary, `AWS_ENDPOINT_URL=http://127.0.0.1:4566`) |
| 6379 | ElastiCache proxy |
| 6400 | MemoryDB proxy |
| 7001 | RDS proxy (PostgreSQL/MySQL) |
| 8182 | Neptune Gremlin proxy |
| 4500 | Web console sidecar (`http://127.0.0.1:4566/_floci/ui`) |

## Documentation

- [INSTALLATION.md](INSTALLATION.md) — prerequisites & verified steps
- [CONFIGURATION.md](CONFIGURATION.md) — `.env` reference, ports, storage modes
- [SECURITY.md](SECURITY.md) — Docker socket implications, firewall, audit
- [README-DEPLOYMENT.md](README-DEPLOYMENT.md) — deployed-state overview, quick commands, safety rules
- [BACKUP-RESTORE.md](BACKUP-RESTORE.md) — what/how to back up and restore
- [AI-INTEGRATION.md](AI-INTEGRATION.md) — use Floci S3/DynamoDB/SQS/Lambda/Secrets in AI projects
- [SERVICE-TEST-REPORT.md](SERVICE-TEST-REPORT.md) — 2026-11-06 test results (core 15/15, heavy 4/4)
- [aws-credentials.example](aws-credentials.example) — dummy credential template

## What is NOT committed

- `.env` (real values) — template only. `data/` (runtime AWS inventory dumps;
  may contain account topology), `tunnel/`, logs. See `.gitignore`.
