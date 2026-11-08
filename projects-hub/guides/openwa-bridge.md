# OpenWA Bridge — project guide (auto-reply WhatsApp bridge)

Auto-reply bridge that listens on the OpenWA API and replies to allowed numbers. Runs as container `openwa-bridge` (node:24) on the same Docker network as OpenWA. Source for full deploy steps: `openwa-bridge-deploy/DEPLOY-GUIDE.md` in this repo.

## How it works
- Container `openwa-bridge` (image built from this bundle, node:24), port 127.0.0.1:2787.
- Listens on the OpenWA API webhook (`message.received` events) and replies to whitelisted senders.
- Webhook URL: `http://openwa-bridge:2787/webhook`, signed with WEBHOOK_SECRET.

## Configuration (.env)
```
PORT=2787
OPENWA_BASE=http://openwa-api:2785
OPENWA_KEY=<api-key from data/.api-key>
SESSION_ID=<session id>
WEBHOOK_SECRET=<random secret>
ALLOWED_NUMBERS=917434968124,919824521780,95532957614301
OWN_NUMBER=917434968124
```

**Important — LID handling:** WhatsApp sends new messages with LID-based JIDs (e.g. `95532957614301@lid`, `isLidSender: true`). The bridge normalizes IDs (strips `@...` and non-digits) and compares against `ALLOWED_NUMBERS`, so add BOTH the phone number and its LID. Find the LID in bridge logs: `docker logs openwa-bridge` → `[recv] ... full={...}` shows `from` and `chatId`.

## Deploy steps (summary)
1. Files: `server.mjs`, `Dockerfile`, `docker-compose.yml`, `start-tunnel.sh`, `.env` (mode 600).
2. `.env` from `.env.example` (see above).
3. `docker compose up -d --build` (needs external network `openwa-deploy_default`).
4. Register webhook on OpenWA: `POST /api/sessions/<SESSION_ID>/webhooks` with `{"url":"http://openwa-bridge:2787/webhook","events":["message.received"],"secret":"<WEBHOOK_SECRET>"}`; verify with `GET /api/sessions/<SESSION_ID>/webhooks`.
5. Optional public tunnel: `bash start-tunnel.sh`, then `docker logs cf-bridge | grep trycloudflare` for URL (changes on restart).
6. Test from a whitelisted number; check logs: `[recv]` received, `[skip] not allowed` whitelist mismatch, `[send] 201` auto-reply sent, `[skip] own message` for own number.

## Troubleshooting
- Signature 401 → WEBHOOK_SECRET mismatch; re-register webhook with same secret.
- No webhook events → check registration + same Docker network.
- Sender shows LID → expected; add LID to whitelist (see above).
- Health: `curl http://127.0.0.1:2787/health` → `{"ok":true}`.
