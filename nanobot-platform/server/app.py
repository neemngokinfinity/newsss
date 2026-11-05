"""Nanobot Platform control plane API + static UI host."""
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import agent, auth, config_manager, db, mcp_client, providers, settings

settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("nanobot-platform")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(settings.APP_LOG)],
)

app = FastAPI(title="Nanobot Platform", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

_stop_events = {}


@app.on_event("startup")
def _startup():
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.APP_LOG.parent.mkdir(parents=True, exist_ok=True)
    config_manager.ensure_defaults()
    auth.bootstrap_admin()


@app.middleware("http")
async def access_log(request: Request, call_next):
    started = time.time()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request failed")
        raise
    if not request.url.path.startswith("/api/logs"):
        logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path,
                    response.status_code, (time.time() - started) * 1000)
    return response


def require_user(user: dict = Depends(auth.current_user)):
    return user


# ---------- auth -----------------------------------------------------------

@app.post("/api/auth/login")
def login(payload: dict, request: Request):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    row = db.q1("SELECT * FROM users WHERE username=?", (username,))
    if not row or not auth.verify_password(password, row["password_hash"]):
        # lightweight rate limiting: 8 attempts/minute per IP
        key = f"fail:{request.client.host}"
        n = int(db.get_setting(key, 0)) + 1
        db.set_setting(key, str(n))
        if n > 8:
            raise HTTPException(429, "Too many attempts, try again in a minute")
        db.set_setting(f"fail_ts:{key}", str(int(time.time())))
        raise HTTPException(401, "Invalid credentials")
    db.set_setting(f"fail:{request.client.host}", "0")
    token = auth.create_session(row["id"], request.client.host, request.headers.get("user-agent", ""))
    db.audit(row["username"], "login", {"ip": request.client.host})
    response = JSONResponse({"token": token, "user": {"id": row["id"], "username": row["username"]}})
    response.set_cookie("nb_session", token, httponly=True, samesite="lax", max_age=30 * 86400)
    return response


@app.post("/api/auth/logout")
def logout(request: Request, user: dict = Depends(require_user)):
    token = request.cookies.get("nb_session")
    if not token:
        authh = request.headers.get("authorization", "")
        if authh.lower().startswith("bearer "):
            token = authh[7:].strip()
    if token:
        auth.delete_session(token)
    db.audit(user["username"], "logout")
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: dict = Depends(require_user)):
    return user


@app.get("/api/version")
def version():
    return {"name": "nanobot-platform", "version": "0.1.0", "engine": "nanobot (compatible)"}


# ---------- system ---------------------------------------------------------

def _read_proc(path):
    try:
        return Path(path).read_text()
    except Exception:
        return ""


@app.get("/api/system/status")
def system_status(user: dict = Depends(require_user)):
    mem = {}
    for line in _read_proc("/proc/meminfo").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            mem[k.strip()] = int(v.strip().split()[0]) * 1024
    try:
        stat = _read_proc("/proc/stat").splitlines()[0].split()[1:8]
        cpu_total = sum(int(x) for x in stat)
        idle = int(stat[3])
    except Exception:
        cpu_total, idle = 1, 0
    try:
        load1, load5, load15 = (float(x) for x in _read_proc("/proc/loadavg").split()[:3])
    except Exception:
        load1 = load5 = load15 = 0.0
    try:
        du = os.statvfs(str(settings.DATA_DIR))
        disk = {"total": du.f_blocks * du.f_frsize, "free": du.f_bavail * du.f_frsize, "bsize": du.f_frsize}
    except Exception:
        disk = {}
    hosts = db.q1("SELECT COUNT(*) AS c FROM conversations")
    try:
        uptime = float(_read_proc("/proc/uptime").split()[0])
    except Exception:
        uptime = 0.0
    return {
        "uptime": uptime,
        "cpu": {"load1": load1, "load5": load5, "load15": load15,
                "last_idle": idle, "last_total": cpu_total},
        "mem": {"total": mem.get("MemTotal"), "available": mem.get("MemAvailable"),
                "used": mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)},
        "disk": disk,
        "conversations": hosts["c"] if hosts else 0,
        "version": "0.1.0",
        "time": db.utcnow(),
    }


# ---------- providers ------------------------------------------------------

@app.get("/api/providers")
def providers_list(user: dict = Depends(require_user)):
    return config_manager.list_providers()


@app.post("/api/providers")
def providers_create(payload: dict, user: dict = Depends(require_user)):
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(400, "name required")
    if config_manager.get_provider(name):
        raise HTTPException(409, "provider already exists")
    return config_manager.upsert_provider(name, payload)


@app.put("/api/providers/{name}")
def providers_update(name: str, payload: dict, user: dict = Depends(require_user)):
    if not config_manager.get_provider(name):
        raise HTTPException(404, "not found")
    return config_manager.upsert_provider(name, payload)


@app.delete("/api/providers/{name}")
def providers_delete(name: str, user: dict = Depends(require_user)):
    config_manager.delete_provider(name)
    return {"ok": True}


@app.post("/api/providers/{name}/test")
def providers_test(name: str, user: dict = Depends(require_user)):
    p = config_manager.get_provider(name)
    if not p:
        raise HTTPException(404, "not found")
    return providers.test_provider(p)


# ---------- MCP servers ----------------------------------------------------

@app.get("/api/mcpservers")
def mcp_list(user: dict = Depends(require_user)):
    return config_manager.list_mcp_servers()


@app.post("/api/mcpservers")
def mcp_create(payload: dict, user: dict = Depends(require_user)):
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(400, "name required")
    return config_manager.upsert_mcp_server(name, payload)


@app.put("/api/mcpservers/{name}")
def mcp_update(name: str, payload: dict, user: dict = Depends(require_user)):
    if not config_manager.get_mcp_server(name):
        raise HTTPException(404, "not found")
    return config_manager.upsert_mcp_server(name, payload)


@app.delete("/api/mcpservers/{name}")
def mcp_delete(name: str, user: dict = Depends(require_user)):
    config_manager.delete_mcp_server(name)
    return {"ok": True}


@app.post("/api/mcpservers/{name}/test")
def mcp_test(name: str, user: dict = Depends(require_user)):
    s = config_manager.get_mcp_server(name)
    if not s:
        raise HTTPException(404, "not found")
    try:
        c = mcp_client.MCPClient(s["url"], s.get("headers"), s.get("transport", "http"))
        c.initialize()
        tools = c.tools_list()
        return {"ok": True, "tools": len(tools), "capabilities": c.capabilities}
    except mcp_client.UnsupportedTransport as e:
        return {"ok": False, "detail": str(e)}
    except mcp_client.MCPError as e:
        return {"ok": False, "detail": str(e)}
    except Exception as e:
        return {"ok": False, "detail": f"{type(e).__name__}: {e}"}


# ---------- tools ----------------------------------------------------------

_TOOL_CACHE = {"ts": 0, "tools": []}


def discover_tools(force=False):
    now = time.time()
    if not force and now - _TOOL_CACHE["ts"] < 15:
        return _TOOL_CACHE["tools"]
    tools = []
    for s in config_manager.list_mcp_servers():
        if not s.get("enabled", True):
            continue
        try:
            c = mcp_client.MCPClient(s["url"], s.get("headers"), s.get("transport", "http"))
            c.initialize()
            tlist = c.tools_list()
        except Exception as e:
            tools.append({"server": s["name"], "tool": "__server_error__",
                          "error": str(e)[:200]})
            continue
        for t in tlist:
            row = db.q1("SELECT enabled FROM tool_status WHERE server=? AND tool=?",
                        (s["name"], t.get("name")))
            enabled = row["enabled"] if row else True
            tools.append({
                "server": s["name"],
                "name": t.get("name"),
                "description": t.get("description", ""),
                "inputSchema": t.get("inputSchema") or {},
                "enabled": bool(enabled),
            })
    _TOOL_CACHE.update(ts=now, tools=tools)
    return tools


@app.get("/api/tools")
def tools_list(force: bool = False, user: dict = Depends(require_user)):
    return discover_tools(force=force)


@app.post("/api/tools/{server}/{tool}/toggle")
def tool_toggle(server: str, tool: str, user: dict = Depends(require_user)):
    row = db.q1("SELECT enabled FROM tool_status WHERE server=? AND tool=?", (server, tool))
    current = bool(row["enabled"]) if row else True
    enabled = 0 if current else 1
    db.exe("INSERT INTO tool_status (server, tool, enabled) VALUES (?,?,?) "
           "ON CONFLICT(server, tool) DO UPDATE SET enabled=excluded.enabled",
           (server, tool, enabled))
    db.audit(user["username"], "tool_toggle", {"server": server, "tool": tool, "enabled": enabled})
    return {"enabled": bool(enabled)}


@app.post("/api/tools/execute")
def tool_execute(payload: dict, user: dict = Depends(require_user)):
    server = str(payload.get("server", ""))
    tool = str(payload.get("tool", ""))
    args = payload.get("args") or {}
    row = db.q1("SELECT enabled FROM tool_status WHERE server=? AND tool=?", (server, tool))
    if row and not row["enabled"]:
        raise HTTPException(403, "tool disabled")
    s = config_manager.get_mcp_server(server)
    if not s:
        raise HTTPException(404, "server not found")
    try:
        c = mcp_client.MCPClient(s["url"], s.get("headers"), s.get("transport", "http"))
        c.initialize()
        result = c.call_tool(tool, args)
    except mcp_client.MCPError as e:
        result = {"isError": True, "content": str(e)}
    except Exception as e:
        result = {"isError": True, "content": f"{type(e).__name__}: {e}"}
    db.exe("INSERT INTO tool_runs (ts, server, tool, args, status, result) VALUES (?,?,?,?,?,?)",
           (db.utcnow(), server, tool, json.dumps(args), "error" if result.get("isError") else "ok",
            json.dumps(result, ensure_ascii=False)[:20000]))
    db.audit(user["username"], "tool_execute", {"server": server, "tool": tool})
    return result


@app.get("/api/tools/runs")
def tool_runs(limit: int = 30, user: dict = Depends(require_user)):
    return [dict(r) for r in db.q(
        "SELECT * FROM tool_runs ORDER BY id DESC LIMIT ?", (min(limit, 200),))]


# ---------- chat / conversations ------------------------------------------

@app.post("/api/conversations")
def conversation_create(payload: dict, user: dict = Depends(require_user)):
    cid = db.exe(
        "INSERT INTO conversations (agent, provider, model, title, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?)",
        (payload.get("agent"), payload.get("provider"), payload.get("model"),
         payload.get("title") or "New chat", db.utcnow(), db.utcnow()))
    return {"id": cid, "title": payload.get("title") or "New chat"}


@app.get("/api/conversations")
def conversation_list(user: dict = Depends(require_user)):
    return [dict(r) for r in db.q(
        "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 200")]


@app.get("/api/conversations/{cid}/messages")
def conversation_messages(cid: int, user: dict = Depends(require_user)):
    rows = db.q("SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (cid,))
    return [dict(r) for r in rows]


@app.delete("/api/conversations/{cid}")
def conversation_delete(cid: int, user: dict = Depends(require_user)):
    db.exe("DELETE FROM messages WHERE conversation_id=?", (cid,))
    db.exe("DELETE FROM conversations WHERE id=?", (cid,))
    db.audit(user["username"], "conversation_delete", {"id": cid})
    return {"ok": True}


@app.post("/api/chat")
def chat(payload: dict, user: dict = Depends(require_user)):
    """SSE streaming chat. Body: {message, agent?, provider?, model?, conversation_id?}"""
    provider_name = payload.get("provider") or None
    model = payload.get("model") or None
    agent_name = payload.get("agent")
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(400, "message required")

    # resolve config
    if agent_name:
        ag = config_manager.get_agent(agent_name)
        if ag:
            provider_name = provider_name or ag.get("provider") or None
            model = model or ag.get("model") or None
    if not provider_name or not model:
        raise HTTPException(400, "provider and model are required (configure them in Settings/Agents)")

    pc = config_manager.get_provider(provider_name)
    if not pc:
        raise HTTPException(404, f"provider '{provider_name}' not configured")

    cid = payload.get("conversation_id")
    if not cid:
        cid = db.exe(
            "INSERT INTO conversations (agent, provider, model, title, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (agent_name, provider_name, model, message[:60], db.utcnow(), db.utcnow()))
    else:
        db.exe("UPDATE conversations SET updated_at=? WHERE id=?", (db.utcnow(), cid))

    db.exe("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?,?,?,?)",
           (cid, "user", message, db.utcnow()))

    allowed_servers = None
    if agent_name:
        ag = config_manager.get_agent(agent_name)
        if ag:
            allowed_servers = set(ag.get("mcpServers") or [])
    if payload.get("tools") is False:
        servers = []
    else:
        servers = [s for s in config_manager.list_mcp_servers()
                   if s.get("enabled", True) and
                   (allowed_servers is None or s["name"] in allowed_servers)]

    stop_event = threading.Event()
    _stop_events[cid] = stop_event

    def gen():
        text_parts = []
        try:
            yield _sse("meta", {"conversation_id": cid, "provider": provider_name, "model": model})
            ag = agent.Agent(
                provider_cfg=pc, model=model,
                system_prompt=None,
                temperature=payload.get("temperature", 0.7),
                tool_servers=servers,
                stop_event=stop_event,
            )
            hist = [{"role": "user", "content": message}]
            for ev in ag.run(hist):
                if ev["type"] == "text":
                    text_parts.append(ev["text"])
                    yield _sse("delta", ev)
                elif ev["type"] == "tool_start":
                    yield _sse("tool_start", ev)
                elif ev["type"] == "tool_end":
                    yield _sse("tool_end", ev)
                elif ev["type"] == "error":
                    yield _sse("error", ev)
                elif ev["type"] == "done":
                    yield _sse("done", {})
                elif ev["type"] == "stopped":
                    yield _sse("stopped", {})
        finally:
            full = "".join(text_parts).strip()
            if full:
                db.exe("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?,?,?,?)",
                       (cid, "assistant", full, db.utcnow()))
                db.exe("UPDATE conversations SET updated_at=? WHERE id=?", (db.utcnow(), cid))
            _stop_events.pop(cid, None)
            stop_event.set()

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/chat/{cid}/stop")
def chat_stop(cid: int, user: dict = Depends(require_user)):
    ev = _stop_events.get(cid)
    if ev:
        ev.set()
        return {"ok": True}
    return {"ok": False, "detail": "no active stream"}


def _sse(event: str, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ---------- files ----------------------------------------------------------

@app.post("/api/files")
def upload_file(file: UploadFile = File(...), user: dict = Depends(require_user)):
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe = Path(file.filename or "file").name
    dest = settings.UPLOAD_DIR / safe
    counter = 1
    while dest.exists():
        dest = settings.UPLOAD_DIR / f"{Path(safe).stem}_{counter}{Path(safe).suffix}"
        counter += 1
    data = file.file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, "file too large")
    dest.write_bytes(data)
    db.audit(user["username"], "file_upload", {"name": safe, "size": len(data)})
    return {"name": dest.name, "size": len(data)}


@app.get("/api/files")
def files_list(user: dict = Depends(require_user)):
    out = []
    if settings.UPLOAD_DIR.exists():
        for p in settings.UPLOAD_DIR.iterdir():
            if p.is_file():
                out.append({"name": p.name, "size": p.stat().st_size,
                            "modified": db.utcnow()})
    return sorted(out, key=lambda f: f["name"])


@app.get("/api/files/{name}")
def file_get(name: str, user: dict = Depends(require_user)):
    safe = Path(name).name
    p = settings.UPLOAD_DIR / safe
    if not p.exists():
        raise HTTPException(404, "not found")
    return FileResponse(p, filename=safe)


@app.delete("/api/files/{name}")
def file_delete(name: str, user: dict = Depends(require_user)):
    safe = Path(name).name
    p = settings.UPLOAD_DIR / safe
    if p.exists():
        p.unlink()
        db.audit(user["username"], "file_delete", {"name": safe})
    return {"ok": True}


# ---------- logs / audit / settings ---------------------------------------

@app.get("/api/logs")
def get_logs(lines: int = 200, user: dict = Depends(require_user)):
    try:
        text = settings.APP_LOG.read_text(errors="replace")
    except Exception:
        return {"lines": []}
    return {"lines": text.splitlines()[-min(lines, 1000):]}


@app.get("/api/audit")
def get_audit(limit: int = 100, user: dict = Depends(require_user)):
    return [dict(r) for r in db.q(
        "SELECT * FROM audit ORDER BY id DESC LIMIT ?", (min(limit, 500),))]


@app.get("/api/settings")
def settings_get(user: dict = Depends(require_user)):
    return {"theme": db.get_setting("ui.theme", "dark"),
            "showToolCalls": db.get_setting("ui.showToolCalls", "1")}


@app.put("/api/settings")
def settings_put(payload: dict, user: dict = Depends(require_user)):
    if "theme" in payload:
        db.set_setting("ui.theme", payload["theme"])
    if "showToolCalls" in payload:
        db.set_setting("ui.showToolCalls", str(payload["showToolCalls"]))
    return {"ok": True}


# ---------- agents ---------------------------------------------------------

def _save_agent_body(name, data):
    llm = data.get("llm") or {}
    config_manager.save_agent(name, {
        "title": data.get("title") or name,
        "description": data.get("description", ""),
        "provider": llm.get("provider") or data.get("provider", ""),
        "model": llm.get("model") or data.get("model", ""),
        "temperature": data.get("temperature", 0.7),
        "mcpServers": data.get("mcpServers") or [],
        "tools": data.get("tools") or [],
        "body": data.get("prompt", ""),
    })


@app.get("/api/config/agents")
def agents_list(user: dict = Depends(require_user)):
    return config_manager.list_agents()


@app.post("/api/config/agents")
def agents_create(payload: dict, user: dict = Depends(require_user)):
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(400, "name required")
    if config_manager.get_agent(name):
        raise HTTPException(409, "agent already exists")
    _save_agent_body(name, payload)
    return {"ok": True}


@app.put("/api/config/agents/{name}")
def agents_update(name: str, payload: dict, user: dict = Depends(require_user)):
    if not config_manager.get_agent(name):
        raise HTTPException(404, "not found")
    _save_agent_body(name, payload)
    return {"ok": True}


@app.delete("/api/config/agents/{name}")
def agents_delete(name: str, user: dict = Depends(require_user)):
    config_manager.delete_agent(name)
    return {"ok": True}


# ---------- static UI ------------------------------------------------------

UI_DIR = settings.BASE_DIR / "ui"
if UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")