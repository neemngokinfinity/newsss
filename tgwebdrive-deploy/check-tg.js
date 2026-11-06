const db = require('better-sqlite3')('data/tgdrive.sqlite');
for (const tbl of ['api_keys','shares','sessions']) {
  const cols = db.prepare('PRAGMA table_info(' + tbl + ')').all().map(c => c.name);
  console.log(tbl + ':', cols.join(','));
}
