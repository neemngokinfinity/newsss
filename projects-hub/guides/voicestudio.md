# VoiceStudio — project guide (AI voice platform)

VoiceStudio (debpalash/VoiceStudio, AGPL-3.0) deployed headless with OmniVoice TTS engine. Full deploy guide in `voicestudio-deploy/DEPLOY-GUIDE.md` in this repo. Container `omnivoice-studio` (image `ghcr.io/debpalash/voicestudio:stable`; Docker Hub mirror `palashdeb/omnivoice-studio:stable`; linux/amd64 only, arm64 via `:stable-cuda-arm64`; do NOT build from source). Sidecar `cf-voicestudio` tunnels `http://omnivoice-studio:3900` — no host port published; app reachable only via tunnel.

## Deploy summary
1. `cp .env.example .env; chmod 600 .env`.
2. `.env` keys:
   - `OMNIVOICE_API_KEY` — required; strong random (`python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`). Admin gate; UI exchanges it for a short-lived session key.
   - `OMNIVOICE_DATA_DIR=/app/omnivoice_data` (must match compose volume)
   - `OMNIVOICE_ANALYTICS_DISABLED=1`
   - `OMNIVOICE_ALLOWED_HOSTS` / `OMNIVOICE_ALLOWED_ORIGINS` — set AFTER tunnel is up
3. `docker compose up -d omnivoice-studio` — first run pulls image (~4.3GB), migrations auto-run; `GET /health` → 503 while initializing, 200 when ready. Model weights NOT auto-downloaded (licence acceptance policy).
4. `docker compose up -d cf-voicestudio`, then get URL: `docker logs cf-voicestudio 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1`.
5. When tunnel URL changes (every restart): update `.env` ALLOWED_HOSTS/ORIGINS with new hostname, `docker compose up -d omnivoice-studio` to recreate, verify 200.

## TTS (OmniVoice engine)
- Engine k2-fsa/OmniVoice — zero-shot, 600+ languages, ~2.4–3.1GB; NOT license-gated (only supertonic3/pockettts are gated — no acceptance needed).
- Speech API (OpenAI-compatible): `POST /v1/audio/speech` with `{"model":"omnivoice","input":"<text ≤4096 chars>","voice":"default","response_format":"wav"}`, header `Authorization: Bearer $OMNIVOICE_API_KEY`. OpenAI voice/model aliases accepted.
- Admin/session: `POST /api/auth/session` (one-time exchange); `GET /models`, `POST /models/install {model_id:...}`, `/setup/download-stream`; `/engines` shows availability (active=omnivoice, active_model=k2-fsa/OmniVoice; evidence_state=not_loaded → model lazy-loads per request).
- Voice profiles: optional `voice` field with profile-id/name instead of "default".

## Tokenizer cache note
If TTS returns 503, the HF cache for `eustlb/higgs-audio-v2-tokenizer` (rev 528e871c2a26c4f0f7773b9754e2e1acae20899d) may be missing. Populate it (config.json, model.safetensors, preprocessor_config.json, README.md, .gitattributes with blobs/<sha256> + symlinks `snapshots/<rev>/<file> → ../../blobs/<hash>`); helper script `populate_tokenizer_cache.sh` in workspace.

## Backups / data
`./data` holds DB + model/HF cache; back up whole `data/` for full restore. HF_HOME=`/app/omnivoice_data/huggingface`.

## Optional cleanup (VPS)
2 Whisper models (~387MB, sherpa-onnx-whisper-tiny + Systran/faster-whisper-base) unused by OmniVoice TTS and safe to remove; old `tgtest` dir (~32M junk).
