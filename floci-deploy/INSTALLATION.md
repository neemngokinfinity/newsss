# Floci — Installation

Verified on: Debian/Ubuntu VPS, Docker 29.1.3, Docker Compose 2.40.3.
Node.js not required for the compose route (only needs Docker).

## 1. Prerequisites

```bash
docker --version          # 24+ recommended
docker compose version     # 2.x
```

## 2. Pull image

```bash
docker pull floci/floci:2.4.0
```

## 3. Configure

Copy the template and edit:

```bash
cp .env.example .env
chmod 600 .env
```

Do NOT commit `.env`. For Lambda support, Floci needs access to the Docker
socket (`/var/run/docker.sock`), already wired in `docker-compose.yml`.

## 4. Start

```bash
docker compose up -d
```

Wait for health:

```bash
docker inspect floci --format '{{.State.Health.Status}}'
# keep polling until → "healthy" (usually <60s)
```

Ready marker in logs:

```bash
docker logs --tail 20 floci
# → "=== AWS Local Emulator Ready ==="
```

## 5. Verify

```bash
# Core services
curl -s http://127.0.0.1:4566/_localstack/health | python3 -m json.tool
# Expect "s3": "available", "dynamodb": "available", "sqs": "available", …

# S3 round-trip
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 \
  aws --endpoint-url=http://127.0.0.1:4566 s3 mb s3://demo-bucket

# DynamoDB
aws --endpoint-url=http://127.0.0.1:4566 dynamodb list-tables
```

## 6. Troubleshooting

| Symptom | Fix |
|---|---|---|
| Container exits on start | Check `docker logs floci`; missing `.env` vars |
| Lambda "docker not available" | Socket mount missing; open `/var/run/docker.sock` |
| Port conflicts (e.g. 6379) | Edit ports in compose; update clients |
| Disk full | Prune: `docker system prune -af`; keep `floci-data` volume |

## 7. Notes

- Image variant: official `floci/floci:2.4.0`.
- Data (S3 bucket contents, DynamoDB tables, etc.) persists in volume `floci-data`.
- Details: [CONFIGURATION.md](CONFIGURATION.md), [SECURITY.md](SECURITY.md).
