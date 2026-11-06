# Long-term Memory (sanitized example)

This file is the template for `memory/MEMORY.md`. Real installations replace
the example sections with their own durable facts. No secrets, tokens, or
private history go in here long-term — infra facts and project state only.

## Project Context

### Example: Web service deployment
- Service container `web-1` (image `example/app:latest`), port `127.0.0.1:8080`.
- Env lives in `.env` (mode 600); `.env.example` is the only thing committed.
- Database volume `app_pgdata` must not be deleted.

### Example: GitHub strategy
- Repo `owner/repo` (public, branch `main`) is the backup home.
- PAT is fine-grained: Contents read/write on that repo only.
- Push bundles in small batches; never commit `.env` or private logs.

## Important Notes

- Keep this file updated with durable facts; strip resolved task state
  (old commit hashes, one-off deployment status) when consolidating.
- History is append-only in `history.jsonl` — do not rewrite it.
