# Floci — Security

## Threat model

Floci emulates AWS locally. It is a **development tool**, not production:
- It listens on loopback only, but any local process can reach it.
- Lambda execution uses your **Docker socket** (runs containers you control
  only if the host is trusted; the socket has host root-equivalent access).

## Rules

1. **Never expose the emulator to the public internet.** Ports are bound to
   `127.0.0.1`. Do NOT change to `0.0.0.0`.
2. **Use the auth string.** Keep `FLOCI_AUTH_STRING` set (default `test:test`;
   override in `.env`, chmod 600).
3. **Docker socket access** is required for real Lambda execution (mount
   `/var/run/docker.sock`). If you don't need Lambda, remove the mount.
4. **No real AWS credentials.** Only dummy `test`/`test`. Real keys must
   never enter this stack or any repo.
5. **Keep `.env` out of git** (see `.gitignore`). Audit files in `data/`
   (IAM/Cognito dumps) are never committed.

## Audit

- `docker logs floci` for unexpected requests/errors.
- `docker stats` while load-testing.
- Review enabled services in `FLOCI_SERVICES`; disable unused ones.

See [BACKUP-RESTORE.md](BACKUP-RESTORE.md) for data safety.
