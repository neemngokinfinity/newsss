# nanobot-profile — Agent Identity & Config Backup

Clean backup of nanobot's identity/persona files (no private history, no secrets).

## Included
- `SOUL.md` — persona (nanobot 🐈)
- `USER.md` — user profile template
- `AGENTS.md` / `HEARTBEAT.md` / `README.md` — agent runtime docs
- `prompts/` — prompt library

## Excluded (privacy)
- `memory/` (MEMORY.md, history.jsonl) — private conversation history
- `.env` files — secrets
- `cron/jobs.json`, `triggers/`, `.nanobot/tool-results/` — runtime state

## Restore
Copy these files back into a nanobot workspace root to restore identity.
