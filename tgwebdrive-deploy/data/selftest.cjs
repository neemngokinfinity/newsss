// TGWebDrive REST API selftest (runs inside container)
const crypto = require('node:crypto');
const db = require('better-sqlite3')('data/tgdrive.sqlite');
const BASE = 'http://127.0.0.1:3001';

const key = 'tdk_selftest';
const keyHash = crypto.createHash('sha256').update(key).digest('hex');
const acc = db.prepare('SELECT id FROM accounts LIMIT 1').get();
if (!acc) { console.log('FAIL: no telegram account'); process.exit(1); }
const existing = db.prepare('SELECT id FROM api_keys WHERE token_hash=?').get(keyHash);
if (!existing) {
  db.prepare('INSERT INTO api_keys (id,token_hash,label,account_id,created_at) VALUES (?,?,?,?,?)')
    .run('k_selftest', keyHash, 'selftest', acc.id, Date.now());
}

async function api(path, opts = {}) {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: { 'x-api-key': key, ...(opts.headers || {}) },
  });
  const text = await res.text();
  let json = null;
  try { json = JSON.parse(text); } catch {}
  return { status: res.status, json, text };
}

let failures = 0;
function check(name, ok, extra = '') {
  console.log((ok ? 'PASS' : 'FAIL') + ' | ' + name + (extra ? ' | ' + extra : ''));
  if (!ok) failures++;
}

(async () => {
  // 1. folders listing
  const f = await api('/api/v1/folders');
  check('list folders', f.status === 200 && Array.isArray(f.json?.folders) && f.json.folders.length >= 1,
    JSON.stringify(f.json?.folders?.map(x => x.title)));
  const folderId = f.json?.folders?.[0]?.id;

  // 2. upload disposable file
  const content = 'tgdrive-selftest-' + Date.now() + '-payload';
  const up = await api('/api/v1/files?folder=' + folderId, {
    method: 'POST',
    headers: {
      'x-filename': encodeURIComponent('selftest.txt'),
      'x-filesize': String(Buffer.byteLength(content)),
      'x-caption': encodeURIComponent('selftest'),
      'content-type': 'application/octet-stream',
    },
    body: content,
  });
  const fileId = up.json?.file?.id;
  check('upload file', up.status === 200 && !!fileId, 'id=' + fileId);

  // 3. download raw + compare
  if (fileId) {
    const dl = await api('/api/v1/files/' + fileId + '/raw?folder=' + folderId);
    check('download raw matches', dl.status === 200 && dl.text === content, 'bytes=' + dl.text.length);
  }

  // 4. delete disposable file
  if (fileId) {
    const del = await api('/api/v1/files?folder=' + folderId + '&ids=' + fileId, { method: 'DELETE' });
    check('delete file', del.status === 200 && del.json?.deleted === 1);
  }

  console.log(failures === 0 ? 'SELFTEST: ALL PASS' : 'SELFTEST: FAILURES=' + failures);
  process.exit(failures === 0 ? 0 : 1);
})();
