# OpenWA WhatsApp Bridge (openwa-bridge)

Auto-reply bridge for OpenWA sessions. Receives WhatsApp messages via webhook and replies with a configurable auto-reply, with number whitelist control.

## Architecture

```
WhatsApp --> OpenWA API (openwa-api:2785, session "nanobot")
              | (webhook event: message.received, HMAC-signed)
              v
        openwa-bridge (node, port 2787)
              | (filter: whitelist + skip own)
              v
        send-text reply to sender chatId
```

## Files

- `server.mjs` — bridge server: webhook endpoint, HMAC signature verification, whitelist matching, auto-reply sender.
- `Dockerfile` — builds `openwa-bridge:latest` (node:24-alpine).
- `docker-compose.yml` — container `openwa-bridge`, port 127.0.0.1:2787, env_file `.env`, network `openwa-deploy_default`.
- `start-tunnel.sh` — optional Cloudflare quick tunnel (`cf-bridge`) for public testing.
- `.env.example` — config template (no secrets).

## Current status

- Bridge running in container `openwa-bridge` (restart=unless-stopped).
- Whitelist includes both phone numbers and the LID of number 2:
  `917434968124` (own), `919824521780` (allowed), `95532957614301` (LID of +919824521780 — WhatsApp sends LID-based JIDs).
