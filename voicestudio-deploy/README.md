# VoiceStudio — VPS deploy (no-secrets bundle)

Self-hosted AI voice platform ([debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio),
AGPL-3.0). This bundle deploys it on the nanobot VPS behind a Cloudflare quick
tunnel. No host port is published; access is via the tunnel URL only.

## Files

- `docker-compose.yml` — two services:
  - `omnivoice-studio`: official image `ghcr.io/debpalash/voicestudio:stable`,
    healthcheck on `/health`, data bind `./data:/app/omnivoice_data` (persists
    everything incl. HF cache).
  - `cf-voicestudio`: cloudflared quick-tunnel sidecar to
    `http://omnivoice-studio:3900` (starts only after studio is healthy).
- `.env.example` — template; copy to `.env` on the server (mode 600).
- `DEPLOY-GUIDE.md` — step-by-step install + tunnel-URL update procedure.

## License notes

- App is AGPL-3.0-only.
- Bundled `omnivoice/` package: Apache-2.0.
- k2-fsa/OmniVoice pretrained weights: CC-BY-NC **(noncommercial)** — they are
  NOT the default engine here; models are never auto-downloaded and are installed
  only after explicit user confirmation (`backend/config/model_licenses.json`
  tracks per-model records).
