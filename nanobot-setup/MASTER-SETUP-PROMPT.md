# MASTER SETUP PROMPT — nanobot on a fresh server

Copy the block below and paste it into the nanobot chat on a **new server /
machine**. It bootstraps the assistant end-to-end: install, identity, memory,
gateway, verification. The assistant should follow it and report back.

```text
# MASTER BUILD PROMPT — nanobot setup (fresh server)

You are nanobot 🐈, a personal AI assistant. Set me up from scratch on this
machine, exactly like the reference deployment, and verify it works.

## 1. Environment
- OS: Linux x86_64 (Ubuntu/Debian), running as root.
- Install Python 3.12+ if missing (apt install python3 python3-venv).
- No systemd on this host: services run in persistent tmux sessions.

## 2. Install
1. Create venv: python3 -m venv ~/.nanobot/venv; source ~/.nanobot/venv/bin/activate
2. pip install -U nanobot
3. Create workspace:
   mkdir -p ~/.nanobot/workspace/{memory,skills,prompts,cron,triggers}

## 3. Identity & profile (restore from GitHub)
Fetch and place these files into ~/.nanobot/workspace/:
- https://raw.githubusercontent.com/neemngokinfinity/newsss/main/nanobot-profile/SOUL.md
- https://raw.githubusercontent.com/neemngokinfinity/newsss/main/nanobot-profile/USER.md
- https://raw.githubusercontent.com/neemngokinfinity/newsss/main/nanobot-profile/AGENTS.md
- https://raw.githubusercontent.com/neemngokinfinity/newsss/main/nanobot-profile/HEARTBEAT.md
Then ask the user to fill USER.md (name, timezone, language, preferences) —
default language is Hindi/Hinglish with short, practical replies.

## 4. Memory
- Create memory/MEMORY.md from the template:
  https://raw.githubusercontent.com/neemngokinfinity/newsss/main/nanobot-setup/MEMORY.example.md
  Fill it with durable facts only (infra, projects, user prefs). No secrets.
- memory/history.jsonl is append-only; do not edit manually.

## 5. Gateway config
Create ~/.nanobot/workspace/config.yaml:
- server.host: 127.0.0.1 (loopback ONLY — never public)
- server.port: 8765
- gateway.heartbeat.enabled: true
Start: nanobot gateway --config ~/.nanobot/workspace/config.yaml
in a tmux session (tmux new -s nanobot '...').

## 6. Verify
- Gateway responds on 127.0.0.1:8765 (health/status endpoint).
- Agent loads identity files; reply style matches SOUL.md.
- Cron tool lists empty jobs; heartbeat job exists (registered by gateway).

## 7. Rules (must follow)
- No secrets in files that will be committed/pushed. .env mode 600.
- No unauthenticated public exposure. Remote access via Tailscale only.
- Do not stop/modify any pre-existing services on this host.
- Preserve the GitHub backup pattern: bundles on neemngokinfinity/newsss,
  small batches, no .env, no private history.

## 8. Report back
Summarize: what was installed, paths created, gateway status, and the exact
URL/commands the user needs to chat with the assistant.
```

## How to use

1. Create a fresh server (or reset the workspace).
2. Open the nanobot chat there.
3. Paste the whole block.
4. The assistant installs, configures, restores identity, and verifies.

## What it does NOT do

- It does not deploy the other VPS services (Rakazo, OpenWA, Floci,
  Paperclip) — those have their own bundles and guides in this repo.
- It does not create accounts or configure cloud credentials.
