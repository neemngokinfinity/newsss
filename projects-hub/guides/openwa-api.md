# OpenWA API — project guide (WhatsApp gateway)

OpenWA (fork of devlikeapro/OpenWA) runs as a Docker container and exposes a REST API to send/receive WhatsApp messages. Deployed on the nanobot VPS. Bundle: `openwa-deploy/` in this repo (scripts only — see below for the API usage).

## Container
- Image `rmyndndharis/openwa:latest`, container `openwa-api`, port 127.0.0.1:2785 (loopback only)
- Volume `./data` (sessions persist); `AUTO_START_SESSIONS=true` (sessions auto-start on container restart)
- API key auto-generated on first run at `data/.api-key` (used as `Authorization: Bearer <key>`); never commit it
- `restart: unless-stopped`

## Session lifecycle
1. Create session: `POST /api/sessions` with `{name, phone}` (international format, e.g. `917434968124`).
2. Complete pairing: the API returns/expects QR / OTP / code steps (endpoints under `/api/sessions/:id/`); follow the returned pairing flow.
3. Check status: `GET /api/sessions/:id` → `status: ready` when logged in.

## Send a message
```bash
curl -X POST http://127.0.0.1:2785/api/sessions/<SESSION_ID>/messages/send-text \
  -H "Authorization: Bearer $(cat data/.api-key)" \
  -H "Content-Type: application/json" \
  -d '{"chatId":"917434968124@c.us","text":"hello"}'
```
→ 201 on success. `chatId` format: `<number>@c.us` (or `@lid` for WhatsApp LID-based IDs).

## Webhooks (incoming messages)
Register a webhook to receive events, e.g. `message.received`:
```bash
curl -X POST http://127.0.0.1:2785/api/sessions/<SESSION_ID>/webhooks \
  -H "Authorization: Bearer $(cat data/.api-key)" \
  -H "Content-Type: application/json" \
  -d '{"url":"http://<bridge>:<port>/webhook","events":["message.received"],"secret":"<your-secret>"}'
```
Verify with `GET /api/sessions/<SESSION_ID>/webhooks`.

## Helper scripts (in `openwa-deploy/`)
- `check-sessions` — list sessions + status
- `health-check` — API health
- `send-test` — send a test message
- `register-webhook` — register the bridge webhook

## Notes
- WhatsApp may send new messages using LID-based JIDs (e.g. `95532957614301@lid`, `isLidSender: true`) — whitelists/bridges must handle both phone numbers and LIDs.
- The API key in `data/.api-key` is server-only; never push it or session data to GitHub.
