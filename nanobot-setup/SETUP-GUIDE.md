# Nanobot — Full Setup Guide

Nanobot is a personal AI assistant built on Inception's diffusion LLM
platform. It runs as a local agent with a gateway, a workspace on disk, and
optional integrations (MCP servers, cron, heartbeat, GitHub).

This guide documents **how this exact assistant is set up on the VPS** so it
can be reproduced or restored anywhere.

---

## 1. Architecture

```text
┌──────────────────────────── nanobot gateway ────────────────────────────┐
│  - HTTP API + web/desktop UI (default port 8765, loopback)             │
│  - Agent loop: reads session, calls tools, writes replies              │
│  - Cron scheduler (reminders / recurring tasks)                       │
│  - Heartbeat (background checks, notification-only on change)          │
│  - Tool executor: built-in tools + MCP servers                        │
└──────────────┬───────────────────────────────┬──────────────────────────┘
               │                                │
      workspace/ (all state)            MCP servers (e.g. GitHub)
      └ SOUL.md USER.md AGENTS.md        └ github-mcp-server → GitHub API
      └ memory/MEMORY.md history.jsonl
      └ skills/{name}/SKILL.md
      └ prompts/ (overrides)
      └ cron/ triggers/ (runtime)
```

Key directories under `~/.nanobot/workspace/`:

| Path | Contents |
|---|---|---|
| `SOUL.md` | Persona (who the agent is, tone) |
| `USER.md` | User profile (language, timezone, preferences) |
| `AGENTS.md` | Behavioral instructions (scheduling rules, heartbeat rules) |
| `HEARTBEAT.md` | Background-check task list |
| `memory/MEMORY.md` | Durable long-term memory (infra facts, project state) |
| `memory/history.jsonl` | Append-only conversation history |
| `skills/` | Custom skills (each = folder with `SKILL.md`) |
| `prompts/` | Advanced prompt overrides (`dream.md`, `evaluator.md`) |
| `cron/jobs.json` | Scheduled jobs (managed by the cron tool) |
| `triggers/` | Inbox / processing / runs (runtime) |

---

## 2. Prerequisites

- Linux x86_64 (Ubuntu/Debian works best)
- Python 3.12+ (venv recommended)
- 2 GB RAM minimum (4+ recommended)
- Disk: 5 GB headroom (agent workspace + models/logs)
- Optional: Docker (for MCP servers such as github-mcp-server),
  Tailscale (private remote access)

---

## 3. Fresh install

```bash
# 1. Python venv
python3 -m venv ~/.nanobot/venv
source ~/.nanobot/venv/bin/activate

# 2. Install nanobot (package name per your distribution channel)
pip install -U nanobot

# 3. Create workspace
export NANOBOT_HOME=~/.nanobot
mkdir -p $NANOBOT_HOME/{workspace,memory,skills,prompts,cron,triggers}
```

### 3.1 Identity files

Create `/ copy the five identity files in the workspace root:

- `SOUL.md` — persona (see nanobot-profile/SOUL.md)
- `USER.md` — user profile (already name, timezone, language, preferences)
- `AGENTS.md` — agent instructions (scheduling, heartbeat rules)
- `HEARTBEAT.md` — background task list (may stay empty)
- `prompts/` — optional overrides (see section 7)

These are the same files shipped in `nanobot-profile/` in this repo.

---

## 4. Gateway configuration

The gateway reads a config file (e.g. `config.yaml`). Minimal example:

```yaml
server:
  host: 127.0.0.1   # never expose publicly
  port: 8765
gateway:
  heartbeat:
    enabled: true    # registers protected heartbeat cron job
```

Start it:

```bash
nanobot gateway --config config.yaml
```

On this VPS there is **no systemd**, so services run in persistent sessions
(tmux). Example:

```bash
tmux new -s nanobot 'nanobot gateway --config /root/.nanobot/workspace/config.yaml'
```

---

## 5. Memory

- `memory/MEMORY.md` — write durable facts here (infrastructure, project
  state, user preferences). Structure:
  ```markdown
  # Long-term Memory
  ## Project Context
  ### Project name
  - fact
  ## Important Notes
  - note
  ```
- `memory/history.jsonl` — automatically appended conversation log. Do not
  edit manually; rotate/prune if huge.
- On consolidation, strip resolved task state; keep durable facts only.

See `MEMORY.example.md` for a sanitized template.

---

## 6. Skills

Built-in skills available (from the nanobot package):

- `clawhub` — install skills from the ClawHub registry
- `tmux` — interactive terminal sessions
- `skill-creator` — create/package custom skills
- `image-generation` — generate/edit images
- `memory` — search past conversations
- `weather` — weatherlookups
- `cron` — schedule reminders / recurring tasks
- `nanobot-document` — nanobot usage/FAQ from bundled docs
- `my` — inspect runtime state, session notes

Custom skill format:

```text
skills/my-skill/
└── SKILL.md       # instructions (front-matter optional)
```

Point the agent to the skill root when it needs to load one.

---

## 7. Prompt overrides (`prompts/`)

| File | Effect |
|---|---|---|
| `dream.md` | Overrides Dream memory-consolidation prompt (`/dream-prompt init`) |
| `evaluator.md` | Overrides heartbeat notification gate (must still call `evaluate_notification`) |

Delete/empty a file to return to built-in behavior.

---

## 8. Scheduling

Two mechanisms; use the right one:

- **cron tool** → fixed time/interval tasks, including one-time reminders.
  "Every day at 8am remind me" = cron job. Jobs default to UTC if no timezone
  given; updates retain the job's timezone.
- **HEARTBEAT.md** → flexible background checks that notify only on
  actionable change. No guaranteed timing. Never use it for fixed schedules.

Rules:

- Use the cron **tool**, never write reminders only into `MEMORY.md`
  (that won't notify).
- Don't create a duplicate heartbeat job if the gateway already registered one.

---

## 9. MCP / external tools

MCP servers can be wired (e.g. GitHub): the server runs in its own Docker
container and the agent calls it through the MCP client. No secrets from the
server are stored in the workspace.

---

## 10. GitHub backup (this repo)

The backup strategy used in this repository:

- All bundles are **no-secrets**: real `.env` values, tokens, invite URLs, and
  private history are never committed; only `.env.example` templates and
  sanitized docs.
- The agent's identity (public persona files) lives in `nanobot-profile/`.
- The setup documentation lives in `nanobot-setup/` (this folder).
- Push pattern: small batches, one topic per commit, verify tree after.

---

## 11. Backup & restore (self)

Back up (at least):

- `workspace/` identity files + `memory/` (history + MEMORY.md)
- `skills/`, `prompts/`, `cron/jobs.json`
- gateway `config.yaml` (no secrets inside — keep `.env` separate)

Restore:

```bash
cp -r <backup>/SOUL.md <backup>/USER.md <backup>/AGENTS.md <backup>/HEARTBEAT.md \
     ~/.nanobot/workspace/
cp -r <backup>/memory ~/.nanobot/workspace/
cp -r <backup>/skills <backup>/prompts ~/.nanobot/workspace/
```

---

## 12. Security checklist

- [ ] Gateway binds loopback only; never `0.0.0.0` without auth
- [ ] `.env` mode 600, never committed
- [ ] No unauthenticated public exposure
- [ ] Remote access via Tailscale tunnel (not open ports)
- [ ] MCP servers pin to their own containers & scoped tokens
- [ ] Tokens in environment, not in files

---

## 13. Troubleshooting

| Symptom | Check |
|---|---|---|
| Reminder never fires | cron job uses the cron tool? timezone set? job enabled? |
| Heartbeat silent | `HEARTBEAT.md` has active tasks? gateway registered the job? |
| Agent forgets facts | `MEMORY.md` was edited by consolidation? context overflow? |
| Gateway won't start | port busy? config parsed? logs at gateway start |
| Disk fills up | `docker system df`; prune unused images (see root README) |

---

## 14. User context (this deployment)

- User language: Hindi/Hinglish — replies should be short and practical.
- GitHub: pushes go to `neemngokinfinity/newsss` (fine-grained PAT, contents
  read/write on this repo only).
- Preserve existing services on the VPS; never stop what you didn't start.
