# Paperclip AI — Deployment Log (ONS AI)

Instance: VPS (tailnet tail63b949.ts.net), workspace `/root/.nanobot/workspace/paperclip-deploy/`
Started: 2026-11-06 ~04:55 UTC

## Phase 1 — VPS Audit (results)
- OS: Ubuntu 24.04-style container, kernel 6.1.102 x86_64 (sandbox: no systemd, root user)
- CPU: 2, RAM: 7.88 GiB, Docker overlayfs
- Node v24.22.2 ✅ (needs 24.11+), npm 11.19.1, pnpm ❌ (not required — Docker deployment)
- Docker 29.1.3, Compose v2.40.3 ✅
- Existing services untouched: rakazo (5173), floci (4566/4500), openwa (2785/2786), hermes (35551/8642), nanobot-gateway (8765), cloudflared tunnels (Floci console/API)
- Port 3100 was occupied by Rakazo API — Paperclip moved to 3110.

## Phase 2 — Install (Docker, official image)
- Repo cloned (shallow) → `repo/` (not committed here).
- Published image: ghcr.io/paperclipai/paperclip:latest (12.8GB)
- Compose file: `docker-compose.deploy.yml` — loopback 127.0.0.1:3110→3100, restart=unless-stopped, authenticated/public deployment mode, Postgres 16 sidecar, tmpfs /tmp 512m.
- Secrets: `.env` (mode 600): BETTER_AUTH_SECRET, PAPERCLIP_TOOL_ACTION_SIGNING_SECRET
- Cloudflare quick tunnel (session `cf-pc`) → public URL (regenerates on restart).

## 2026-11-06 — Deploy complete (Phase 2->3 transition)
- Stack RUNNING: paperclip + paperclip-db (healthy).
- Health: 200 {status:ok, deploymentMode:authenticated, deploymentExposure:public, migrations applied}
- Bootstrap invite created (one-time, 72h) — claimed via browser; invite URLs are intentionally NOT stored in this public repo.
- Issues fixed: port conflict 3100 (rakazo) → 3110; /tmp ENOSPC → tmpfs 512m; disk 100% → pruned ~4.5GB unused images (floci test variants, mongo, gremlin, lambda, python slim), freed build cache 3.9GB.
- NOTE: host disk only 40G total; paperclip image 12.8GB. Keep an eye on space (rakazo computer:edge 2.35GB idle is first deletion candidate if needed).
