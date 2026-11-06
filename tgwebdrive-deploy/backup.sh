#!/bin/bash
# Daily backup of TGWebDrive SQLite DB + sessions
set -e
STAMP=$(date +%Y%m%d-%H%M%S)
docker exec -e STAMP="$STAMP" tgwebdrive node -e "const db=require('better-sqlite3')('data/tgdrive.sqlite');const s=process.env.STAMP;db.backup('data/backups/tgdrive-'+s+'.sqlite').then(()=>console.log('backup ok '+s)).catch(e=>{console.error(e);process.exit(1)})"
ls -1t /root/.nanobot/workspace/tgwebdrive-deploy/data/backups/tgdrive-*.sqlite 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "TGWebDrive backup done: ${STAMP}"
