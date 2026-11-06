# Floci — Backup & Restore

## What to back up

- The Docker volume `floci-data` (S3 objects, DynamoDB tables, SQS queues,
  IAM state, logs).
- `.env` (secrets) — store offline, never in git.

## Backup

```bash
# 1. Snapshot volume to a tar on the host
docker run --rm -v floci-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/floci-data-$(date +%F).tgz -C /data .

# 2. Optional: export bucket listing / config as JSON
aws --endpoint-url=http://127.0.0.1:4566 s3 ls --recursive s3:// | tee s3-inventory.txt
```

Keep the tarball off the VPS (download to your machine / object storage).

## Restore

```bash
# 1. Stop the stack
docker compose down

# 2. Restore volume contents from backup
docker run --rm -v floci-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/floci-data-<DATE>.tgz -C /data

# 3. Start again
docker compose up -d
```

## Notes

- For scheduled backups, add a cron entry (e.g. `0 2 * * * docker run ...`).
- Test restore at least once to validate the pipeline.
