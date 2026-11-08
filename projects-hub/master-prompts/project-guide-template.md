# {Project Name} — Deploy Guide

> Template: replace every {placeholder}. Keep it no-secrets — never paste .env,
> tokens, invite URLs, or data dumps. Push the filled-in guide to
> neemngokinfinity/newsss/{project}-deploy/ as part of the sanitized bundle.

## Overview
- **What it does**: {one-line purpose}
- **Stack**: {languages/frameworks/images}
- **Status**: {deployed / ready to deploy / archived}
- **Home on GitHub**: `neemngokinfinity/newsss/{project}-deploy/`

## Architecture
- Container/image: {name} ({image})
- Host ports: {published ports; prefer loopback-only, or tunnel-only}
- Data: {volumes/binds}
- Tunnel: {cloudflared sidecar name → http://<service>:<port>}

## Deployment
1. Create `workspace/{project}-deploy/` with `docker-compose.yml`.
2. Secrets: `.env` with `chmod 600`; never commit it.
3. Pull + up: `docker compose pull && docker compose up -d`.
4. Verify: `docker compose ps`; health endpoint {url}; logs via `docker logs <ctr>`.

## Cloudflare tunnel
- Public URL: {current trycloudflare URL — changes on restart}
- After restart: re-grep `docker logs <tunnel-ctr> | grep trycloudflare`, save the new URL, update {PUBLIC_URL/ALLOWED_HOSTS/ORIGINS} in .env, recreate the app container.

## Verification checklist
- [ ] Health endpoint returns 200
- [ ] Auth/API works (test with a disposable token, not real secrets)
- [ ] Web UI reachable through the tunnel
- [ ] ALLOWED_HOSTS includes the current tunnel host

## Troubleshooting
- {common issue} → {fix}

## Backup
- {cron job / script name}, schedule {when}, rotate {n} copies.

## Sanitized bundle (GitHub)
- Contents: README/DEPLOY-GUIDE.md, compose file, .env.example, scripts.
- Excluded: .env, secrets, invite URLs, data dumps.
