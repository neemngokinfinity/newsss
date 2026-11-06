#!/bin/bash
docker rm -f cf-bridge 2>/dev/null
docker run -d --name cf-bridge --restart unless-stopped \
  --network openwa-deploy_default \
  -e TUNNEL_URL=http://openwa-bridge:2787 \
  cloudflare/cloudflared:latest \
  sh -c "cloudflared tunnel --url \"$TUNNEL_URL\" --no-autoupdate"
