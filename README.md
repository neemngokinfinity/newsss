# newsss — VPS Deployment Bundles

Private backup of deployment configs for services running on the VPS.
**No secrets are committed here** — every bundle ships templates with `.env.example`,
never the real `.env`.

## Contents

- [rakazo-deploy/](rakazo-deploy/) — Rakazo (self-hosted AI platform) deployment: published-image Compose stack, Tailscale overrides, installer scripts, OPS guide, env key inventory.
- [openwa-deploy/](openwa-deploy/) — OpenWA second instance (isolated WhatsApp API Gateway) on the same VPS: compose, OPS guide, env template.
- [floci-deploy/](floci-deploy/) — Floci local AWS emulator (2.4.0) + web console sidecar: compose, install/config/security/backup guides, AWS test report, dummy-credential template.
- [paperclip-deploy/](paperclip-deploy/) — Paperclip AI platform (authenticated/public mode): compose with Postgres sidecar, env template, deployment guide, deploy log.
- [nanobot-platform/](nanobot-platform/) — Nanobot web UI (login, chat, tools, managers, deploy, tests) + backend API surface.
- [nanobot-profile/](nanobot-profile/) — Agent profile (SOUL/USER) and platform docs.

## What runs on the VPS

| Service | Container/scope | Port | Notes |
|---|---|---|---|
| Rakazo | rakazo-api/web/worker/supervisor/postgres | 3100, 5173 | Tailscale-served HTTPS |
| OpenWA (Hermes stack) | openwa-api | 2785 | Existing stack — never touch |
| OpenWA (second, this repo) | openwa-api-2 | 2786 | Isolated SQLite instance |
| Hermes Agent | hermes | 8642 | Existing — never touch |
| Floci | floci + sidecars (UI/RDS/Redis/Neptune) | 4566, 4500, 6379, 6400, 7001, 8182 | Loopback-only AWS emulator |
| Paperclip | paperclip + paperclip-db (Postgres 16) | 3110 (loopback) | Authenticated/public UI via Cloudflare quick tunnel |
| nanobot-gateway / desktop / websockify | pre-existing | 8765, 8080, 6080 | Existing — never touch |

All services bind loopback (`127.0.0.1`) by default. The only public ingress is
the **Paperclip Cloudflare quick tunnel** (login required — authenticated mode).
Quick-tunnel URLs regenerate on tunnel restart; update `PAPERCLIP_PUBLIC_URL`
and `PAPERCLIP_ALLOWED_HOSTNAMES` accordingly.

## VPS setup (generic steps used)

1. **Host prep** — Ubuntu LTS, `apt update && apt upgrade`.
2. **Docker + Compose plugin**:
   ```
   curl -fsSL https://get.docker.com | sh
   ```
   Compose v2 comes with the plugin.
3. **Directory layout** (this VPS):
   ```
   /root/.nanobot/workspace/rakazo          # Rakazo deployment
   /root/.nanobot/workspace/openwa-deploy   # OpenWA second instance
   /root/.nanobot/workspace/floci           # Floci emulator
   /root/.nanobot/workspace/paperclip-deploy # Paperclip AI
   ```
4. **Secrets** — every service has a `.env` (mode 600). Never commit values.
5. **Reboot resilience** — `restart: unless-stopped`; tailscaled must be restarted manually (no systemd on this host) — see OPS.md in each bundle.
6. **Disk** — host has only 40G total; the Paperclip image alone is 12.8G. Keep `docker system df` in check; remove unused test images before they pile up.

## Tailscale (private access)

- Tailnet: `tail63b949.ts.net`, hostname `rakazo-vps` (IP `100.90.125.71`)
- Access URLs (tailnet-only, HTTPS):
  - Rakazo: https://rakazo-vps.tail63b949.ts.net/ (proxy → 127.0.0.1:5173)
  - OpenWA second: add `tailscale serve` for 2786 when needed
- Commands:
  ```
  tailscaled --tun=userspace-networking   # long-running session (no systemd)
  tailscale up --hostname=rakazo-vps
  tailscale serve --bg 5173
  tailscale serve --bg 2786
  tailscale serve status
  ```
- Ports stay loopback-bound (never public).

## Security notes

- `.env` files are never committed; only templates (`.env.example`).
- Back up `ENCRYPTION_KEY` / `BETTER_AUTH_SECRET` (Rakazo, Paperclip) — encrypted content is unrecoverable without them.
- OpenWA master key/pepper live in that instance's `.env` only.
- Floci uses dummy AWS credentials only (`test`/`test`); the `data/` AWS inventory dumps are **not** committed.
- Never modify/stop the Hermes agent or its openwa-api.
