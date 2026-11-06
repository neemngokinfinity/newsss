# DEPLOY GUIDE — OpenWA Bridge

Full step-by-step guide to deploy the auto-reply bridge on the nanobot VPS.

## Prerequisites

- OpenWA API running as container `openwa-api` (image rmyndharis/openwa:latest, port 127.0.0.1:2785, volume `./data`), with a ready session (e.g. `nanobot`, id `cf93668d-...`).
- API key for OpenWA (stored in `data/.api-key`).
- User-defined webhook secret.

## Step 1 — Files

Place this bundle in `workspace/openwa-bridge/`:

- `server.mjs`, `Dockerfile`, `docker-compose.yml`, `start-tunnel.sh`, `.env`

## Step 2 — .env

Create `.env` (mode 600) from `.env.example`:

```
PORT=2787
OPENWA_BASE=http://openwa-api:2785
OPENWA_KEY=<api-key from data/.api-key>
SESSION_ID=<session id>
WEBHOOK_SECRET=<your random secret>
ALLOWED_NUMBERS=917434968124,919824521780,95532957614301
OWN_NUMBER=917434968124
```

`ALLOWED_NUMBERS`: own number + numbers allowed to trigger replies. **Important:** WhatsApp sends new messages with LID-based JIDs (e.g. `95532957614301@lid`, `isLidSender: true`). The bridge normalizes IDs (strips `@...` and non-digits) and compares against this list, so add BOTH the phone number and its LID if replies are skipped. Get the LID from bridge logs: `docker logs openwa-bridge` → `[recv] ... full={...}` shows `from` and `chatId`.

## Step 3 — Build & start

```
cd workspace/openwa-bridge
docker compose up -d --build
```

Requires external network `openwa-deploy_default` (created by OpenWA deploy).

## Step 4 — Register webhook on OpenWA

POST to OpenWA API (substitute values):

```
POST /api/sessions/<SESSION_ID>/webhooks
{
  "url": "http://openwa-bridge:2787/webhook",
  "events": ["message.received"],
  "secret": "<WEBHOOK_SECRET>"
}
```

Verify via `GET /api/sessions/<SESSION_ID>/webhooks`.

## Step 5 — Optional: public tunnel

```
bash start-tunnel.sh
docker logs cf-bridge | grep trycloudflare   # get URL
```

The tunnel URL changes on restart; re-grep and update if you keep a public reference.

## Step 6 — Test

1. Send a message from an allowed number.
2. Check `docker logs openwa-bridge`:
   - `[recv] from=...` — message received (full payload logged).
   - `[skip] not allowed: ...` — whitelist mismatch (add LID/phone to `ALLOWED_NUMBERS`, restart).
   - `[send] 201 ...` — auto-reply sent.
3. Own number messages are skipped (`[skip] own message`).

## Troubleshooting

- **Signature 401**: WEBHOOK_SECRET mismatch — re-register webhook with same secret.
- **No webhook events**: check webhook registration and that bridge is on the same Docker network.
- **Sender shows LID**: expected; ensure LID is in whitelist (see Step 2).
- **Health check**: `curl http://127.0.0.1:2787/health` → `{"ok":true}`.
