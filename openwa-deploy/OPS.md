# OpenWA Second Instance — Ops

Instance: openwa-api-2 (isolated; Hermes openwa-api untouched)
Dir: /root/.nanobot/workspace/openwa-deploy
Image: openwa-openwa-api:latest
Port: 127.0.0.1:2786 -> 2785 (loopback only)
DB: SQLite in volume openwa2_openwa-data
Network: openwa2-net
Dashboard: http://127.0.0.1:2786

## Commands (run from /root/.nanobot/workspace/openwa-deploy)
Start:   docker compose -f docker-compose.second.yml --project-name openwa2 up -d
Status:  docker compose -f docker-compose.second.yml --project-name openwa2 ps
Logs:    docker compose -f docker-compose.second.yml --project-name openwa2 logs -f
Stop:    docker compose -f docker-compose.second.yml --project-name openwa2 down
Restart: docker compose -f docker-compose.second.yml --project-name openwa2 restart

## Secrets
- .env (mode 600) holds API_MASTER_KEY and API_KEY_PEPPER — never commit, never share.
- Log into the dashboard with the master key at first use.

## Safety
- This instance is fully isolated: different container name, volume, network, port.
- Never modify/stop the existing openwa-api (Hermes stack).
