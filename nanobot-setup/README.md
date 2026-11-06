# nanobot-setup — Complete Agent Setup & Kit

Everything needed to understand, reproduce, and restore the **nanobot**
personal AI assistant (the agent that maintains this repo): identity files,
memory conventions, skills, scheduling, and a full setup guide.

## Contents

| Path | What it is |
|---|---|---|
| [SETUP-GUIDE.md](SETUP-GUIDE.md) | Step-by-step deployment & configuration guide (the main document) |
| [PROFILE-BUNDLE.md](PROFILE-BUNDLE.md) | Identity/persona files explained with templates |
| [MEMORY.example.md](MEMORY.example.md) | Sanitized example of the long-term memory file format |

Sibling bundle in this repo: [`nanobot-profile/`](../nanobot-profile/) holds the
**live** identity files (`SOUL.md`, `USER.md`, `AGENTS.md`, `HEARTBEAT.md`, `prompts/`).

## Purpose

- Reproduce the same assistant on another VPS/machine.
- Restore the assistant's identity after a disk reset.
- Document the agent's own architecture, memory, and scheduling for humans.

## Quick restore (if you already have nanobot installed)

```bash
# copy identity files into a workspace root
cp -r nanobot-profile/{SOUL.md,USER.md,AGENTS.md,HEARTBEAT.md,prompts} \
     ~/.nanobot/workspace/
```

See [SETUP-GUIDE.md](SETUP-GUIDE.md) for the full path from zero.
