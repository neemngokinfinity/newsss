# Projects Hub — neemngokinfinity/newsss

Consolidated **project guides** + **master prompts** for every deployment on the nanobot VPS. One place to find how each service works, how it was deployed, and how to rebuild it on a fresh host.

Everything here is sanitized: **no secrets, no .env, no API keys, no invite URLs**. Real configurations stay on the server only.

---

## 📁 Project guides (`guides/`)

| Project | Guide | Full deploy bundle (this repo) |
|---|---|---|
| TGWebDrive (Telegram cloud drive) | [guides/tgwebdrive.md](guides/tgwebdrive.md) | [tgwebdrive-deploy/](../tgwebdrive-deploy/) |
| OpenWA API (WhatsApp gateway) | [guides/openwa-api.md](guides/openwa-api.md) | [openwa-deploy/](../openwa-deploy/) |
| OpenWA auto-reply bridge | [guides/openwa-bridge.md](guides/openwa-bridge.md) | [openwa-bridge-deploy/](../openwa-bridge-deploy/) |
| Obot (AI governance platform) | [guides/obot.md](guides/obot.md) | [obot-deploy/](../obot-deploy/) |
| VoiceStudio (AI voice / TTS) | [guides/voicestudio.md](guides/voicestudio.md) | [voicestudio-deploy/](../voicestudio-deploy/) |
| Nanobot Platform (AI web UI) | [guides/nanobot-platform.md](guides/nanobot-platform.md) | [nanobot-platform/](../nanobot-platform/) |

Each bundle folder contains the actual Dockerfile / compose / scripts / `.env.example`. The hub guides are the consolidated walkthroughs.

---

## 🧠 Master prompts (`master-prompts/`)

Copy-and-paste prompts that bootstrap nanobot / deploy services from scratch:

- [nanobot-master-setup-prompt.md](master-prompts/nanobot-master-setup-prompt.md) — full fresh-server nanobot bootstrap (install, identity, memory, gateway, verify).
- [vps-docker-deploy.md](master-prompts/vps-docker-deploy.md) — the master deploy/tunnel/GitHub-backup workflow used for every VPS service.
- [project-guide-template.md](master-prompts/project-guide-template.md) — reusable template to generate a no-secrets guide for a new project.

---

## 🚀 How to use

1. **New server** → paste `nanobot-master-setup-prompt.md` into nanobot chat.
2. **Deploy a service** → open the matching `guides/` file and follow steps; use `vps-docker-deploy.md` for the generic workflow.
3. **Rebuild** → clone this repo, take the bundle folder (e.g. `tgwebdrive-deploy/`), copy `.env.example` → `.env`, fill secrets, `docker compose up -d`.

---

## ℹ️ Notes

- Cloudflare quick-tunnel URLs change on every tunnel restart — no URLs are stored here; re-grep `docker logs <tunnel-ctr>` for the current one.
- Current deployments (all healthy): tgwebdrive, openwa-api, openwa-bridge, obot, omnivoice-studio (+ cloudflared sidecars).
- Repo home: https://github.com/neemngokinfinity/newsss
