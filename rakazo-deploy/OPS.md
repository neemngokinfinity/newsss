# Rakazo Ops — VPS Deployment

Deployed: 2026-11-05
Location: /root/.nanobot/workspace/rakazo
Images: ghcr.io/elie222/rakazo/app:edge, computer:edge
Stack: postgres, api, worker, web, supervisor, computer (one-shot), data-init (one-shot), migrate (one-shot)

## Commands (run from /root/.nanobot/workspace/rakazo)

Start:      docker compose -f docker-compose.images.yml up -d
Stop:       docker compose -f docker-compose.images.yml down
Restart:    docker compose -f docker-compose.images.yml restart
Status:     docker compose -f docker-compose.images.yml ps
Logs:       docker compose -f docker-compose.images.yml logs -f api worker web postgres supervisor
Inspect:    docker inspect <container>

## Persistent volumes
- rakazo_pgdata: PostgreSQL data
- rakazo_appdata: app data (computers, files)
- rakazo_webassets: static assets

## Secrets
- Stored in .env (permissions 600). Do not print values.
- Back up ENCRYPTION_KEY and BETTER_AUTH_SECRET from .env — encrypted content is unrecoverable without them.

## Notes
- Web binds 127.0.0.1:5173 only; API 127.0.0.1:3100. No public exposure yet.
- Sandbox egress: restricted (supervisor verified).
- Restart policy: unless-stopped on core services.
- Do NOT delete/modify Hermes Agent or openwa stack.

## Tailscale (private Android access)
- IP: 100.90.125.71 (hostname rakazo-vps, tailnet tail63b949.ts.net)
- Access URL (tailnet only, HTTPS): https://rakazo-vps.tail63b949.ts.net/
- Serve config: `tailscale serve status` — proxy to http://127.0.0.1:5173
- Port 5173 stays loopback-only; NOT public. No public exposure.
- Daemon start (no systemd on this host):
  tailscaled --tun=userspace-networking   (long-running session)
  tailscale up --hostname=rakazo-vps
  tailscale serve --bg 5173
- tailscaled currently runs in exec session f40bb621da25 (24h runtime).
- To stop serving: `tailscale serve --https=443 off`
