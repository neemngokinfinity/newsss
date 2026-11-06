import http from 'node:http';
import crypto from 'node:crypto';

const PORT = Number(process.env.PORT || 2787);
const OPENWA_BASE = process.env.OPENWA_BASE || 'http://openwa-api:2785';
const OPENWA_KEY = process.env.OPENWA_KEY || '';
const SESSION_ID = process.env.SESSION_ID || '';
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || '';
const ALLOWED = (process.env.ALLOWED_NUMBERS || '').split(',').map(s => s.trim()).filter(Boolean);
const OWN_NUMBER = (process.env.OWN_NUMBER || '').trim();

function norm(chatId) {
  if (!chatId) return '';
  return chatId.split('@')[0].replace(/\D/g, '');
}
function allowed(chatId) {
  const n = norm(chatId);
  return ALLOWED.some(a => norm(a) === n);
}

function verifySig(req, raw) {
  if (!WEBHOOK_SECRET) return true;
  const sig = req.headers['x-openwa-signature'] || '';
  const expect = 'sha256=' + crypto.createHmac('sha256', WEBHOOK_SECRET).update(raw).digest('hex');
  const a = Buffer.from(sig);
  const b = Buffer.from(expect);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

async function sendText(chatId, text) {
  const r = await fetch(OPENWA_BASE + '/api/sessions/' + SESSION_ID + '/messages/send-text', {
    method: 'POST',
    headers: { 'x-api-key': OPENWA_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({ chatId, text }),
  });
  const t = await r.text();
  console.log('[send]', r.status, chatId, t.slice(0, 200));
  return r.status;
}

async function handleMessage(data) {
  const chatId = data.from || data.sender?.id || data.chatId || data.remoteJid || '';
  const text = (data.body || data.text || '').toString();
  const n = norm(chatId);
  if (!chatId || !text) return;
  console.log('[recv] from=' + n + ' text=' + text.slice(0, 60) + ' full=' + JSON.stringify(data).slice(0, 500));

  if (!allowed(chatId)) {
    console.log('[skip] not allowed: ' + n);
    return;
  }
  if (n && n === norm(OWN_NUMBER)) {
    console.log('[skip] own message');
    return;
  }

  let reply = 'Hi! Ye nanobot ka WhatsApp bridge hai. Aapka message mil gaya: "' + text.slice(0, 120) + '". (auto-reply)';
  await sendText(chatId, reply);
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: true }));
    return;
  }
  if (req.method !== 'POST' || req.url !== '/webhook') {
    res.writeHead(404); res.end(); return;
  }
  let raw = '';
  for await (const chunk of req) raw += chunk;
  if (!verifySig(req, raw)) {
    res.writeHead(401); res.end('bad signature'); return;
  }
  let body; try { body = JSON.parse(raw); } catch { body = {}; }
  res.writeHead(200); res.end('ok');
  const ev = body.event || '';
  if (ev === 'message.received') {
    try { await handleMessage(body.data || {}); } catch (e) { console.error('[err]', e.message); }
  } else {
    console.log('[event]', ev);
  }
});

server.listen(PORT, '0.0.0.0', () => console.log('bridge listening on ' + PORT));
