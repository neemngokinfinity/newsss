# newsss — VPS Deployment Bundles

Private backup of deployment configs for services running on the VPS.
**No secrets are committed here** — every bundle ships templates with `.env.example`,
never the real `.env`.

## Contents

- [rakazo-deploy/](rakazo-deploy/) — Rakazo (self-hosted AI platform) deployment: published-image Compose stack, Tailscale overrides, installer scripts, OPS guide, env key inventory.
- [openwa-deploy/](openwa-deploy/) — OpenWA second instance (isolated WhatsApp API Gateway) on the same VPS: compose, OPS guide, env template.

## What runs on the VPS

| Service | Container/scope | Port | Notes |
|---|---|---|---|
| Rakazo | rakazo-api/web/worker/supervisor/postgres | 3100, 5173 | Tailscale-served HTTPS |
| OpenWA (Hermes stack) | openwa-api | 2785 | Existing stack — never touch |
| OpenWA (second, this repo) | openwa-api-2 | 2786 | Isolated SQLite instance |
| Hermes Agent | hermes | 8642 | Existing — never touch |

All services bind loopback (`127.0.0.1`) only; nothing is exposed publicly.

## VPS setup (generic steps used)

1. **Host prep** — Ubuntu LTS, `apt update && apt upgrade`.
2. **Docker + Compose plugin**:
   ```
   curl -fsSL https://get.docker.com | sh
   ```
   Compose v2 comes with the plugin.
3. **Directory layout**:
   ```
   /opt/rakazo        # Rakazo deployment
   /root/.nanobot/workspace/rakazo   # (this VPS: workspace root)
   /root/.nanobot/workspace/openwa-deploy  # OpenWA second instance
   ```
4. **Secrets** — every service has a `.env` (mode 600). Never commit values.
5. **Firewall/egress** — `restrict-computer-egress.sh` for sandbox egress on Rakazo; OpenWA second instance uses no host bind-mounts.
6. **Reboot resilience** — `restart: unless-stopped`; tailscaled must be restarted manually (no systemd on this host) — see OPS.md in each bundle.

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
- Back up `ENCRYPTION_KEY` / `BETTER_AUTH_SECRET` (Rakazo) — encrypted content is unrecoverable without them.
- OpenWA master key/pepper live in that instance's `.env` only.
- Never modify/stop the Hermes agent or its openwa-api.
