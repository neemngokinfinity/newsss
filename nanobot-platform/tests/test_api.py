"""End-to-end API tests with mock OpenAI-compatible + MCP HTTP servers."""
import json
import os
import tempfile
import threading

os.environ["NANOBOT_PLATFORM_DATA"] = tempfile.mkdtemp(prefix="nbpt-data-")
os.environ["NANOBOT_ADMIN_PASSWORD"] = "testpass123"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.app import app  # noqa: E402

client = TestClient(app)
client.__enter__()  # trigger startup (bootstrap admin, config defaults)


# ---- mock OpenAI-compatible chat server ----------------------------------

class MockLLMHandler:
    def __call__(self, req):
        path = req.path
        body = b""
        length = int(req.headers.get("content-length", 0))
        if length:
            body = req.rfile.read(length)
        if path.endswith("/models"):
            req.send_response(200)
            req.send_header("Content-Type", "application/json")
            req.end_headers()
            req.wfile.write(json.dumps({"object": "list", "data": [{"id": "mock-model"}]}).encode())
            return
        if path.endswith("/chat/completions"):
            data = json.loads(body)
            stream = data.get("stream")
            if stream:
                req.send_response(200)
                req.send_header("Content-Type", "text/event-stream")
                req.end_headers()
                if data.get("tools"):
                    tool = data["tools"][0]
                    delta = {"tool_calls": [{
                        "index": 0, "id": "call_1", "type": "function",
                        "function": {"name": tool["function"]["name"],
                                     "arguments": json.dumps({"q": "x"})},
                    }]}
                    payload = {"choices": [{"delta": delta}]}
                    req.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
                    req.wfile.flush()
                else:
                    for c in ["Hel", "lo ", "world"]:
                        payload = {"choices": [{"delta": {"content": c}}]}
                        req.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
                        req.wfile.flush()
                req.wfile.write(b"data: [DONE]\n\n")
                req.wfile.flush()
            else:
                req.send_response(200)
                req.send_header("Content-Type", "application/json")
                req.end_headers()
                msg = {"role": "assistant", "content": "Hello world"}
                out = {"choices": [{"message": msg}]}
                # support tool_calls echo for tests with tools
                if data.get("tools"):
                    tool = data["tools"][0]
                    out["choices"][0]["message"] = {
                        "role": "assistant", "content": None,
                        "tool_calls": [{
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": tool["function"]["name"],
                                         "arguments": json.dumps({"q": "x"})},
                        }],
                    }
                req.wfile.write(json.dumps(out).encode())
            return
        req.send_response(404)
        req.end_headers()


# ---- mock MCP HTTP server -------------------------------------------------

class MockMCPHandler:
    def __init__(self):
        self.tools = [{
            "name": "echo",
            "description": "Echo back text",
            "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}},
                            "required": ["text"]},
        }]

    def __call__(self, req):
        length = int(req.headers.get("content-length", 0))
        body = req.rfile.read(length) if length else b""
        data = json.loads(body or b"{}")
        method = data.get("method")
        result = {}
        if method == "initialize":
            result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "mock", "version": "1.0"}}
        elif method == "tools/list":
            result = {"tools": self.tools}
        elif method == "tools/call":
            name = data["params"]["name"]
            args = data["params"].get("arguments", {})
            if name == "echo":
                result = {"content": [{"type": "text", "text": args.get("text", "")}],
                          "isError": False}
            else:
                result = {"content": [{"type": "text", "text": "unknown"}], "isError": True}
        else:
            result = {}
        req.send_response(200)
        req.send_header("Content-Type", "application/json")
        req.end_headers()
        req.wfile.write(json.dumps({"jsonrpc": "2.0", "id": data.get("id"), "result": result}).encode())


@pytest.fixture(scope="module")
def llm_mock():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            MockLLMHandler()(self)

        def do_GET(self):
            MockLLMHandler()(self)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/v1"
    srv.shutdown()


@pytest.fixture(scope="module")
def mcp_mock():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            MockMCPHandler()(self)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/mcp"
    srv.shutdown()


# ---- tests ----------------------------------------------------------------

@pytest.fixture(scope="module")
def authed():
    r = client.post("/api/auth/login", json={"username": "admin", "password": "testpass123"})
    assert r.status_code == 200, r.text
    client.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
    yield


def test_auth_required():
    assert client.get("/api/providers").status_code == 401
    assert client.get("/api/system/status").status_code == 401


def test_login():
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
    r = client.post("/api/auth/login", json={"username": "admin", "password": "testpass123"})
    assert r.status_code == 200
    body = r.json()
    assert "token" in body and body["user"]["username"] == "admin"
    client.headers.update({"Authorization": f"Bearer {body['token']}"})


def test_providers_crud(llm_mock, authed):
    r = client.post("/api/providers", json={
        "name": "mockllm", "dialect": "openai-chat", "baseURL": llm_mock,
        "model": "mock-model", "apiKey": "sk-test-123"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["hasKey"] is True and "apiKey" not in body
    lst = client.get("/api/providers").json()
    assert any(p["name"] == "mockllm" and p["apiKey"] == {"env": None, "masked": "•••"} for p in lst)
    t = client.post("/api/providers/mockllm/test").json()
    assert t["ok"] is True, t
    r = client.put("/api/providers/mockllm", json={"model": "mock-model-2"})
    assert r.status_code == 200


def test_mcp_and_tools(mcp_mock, authed):
    r = client.post("/api/mcpservers", json={
        "name": "mockmcp", "url": mcp_mock, "transport": "http"})
    assert r.status_code == 200, r.text
    t = client.post("/api/mcpservers/mockmcp/test").json()
    print("MCP TEST RESULT:", t)
    assert t["ok"] is True and t["tools"] == 1, t
    tools = client.get("/api/tools?force=true").json()
    assert any(x["server"] == "mockmcp" and x["name"] == "echo" for x in tools)
    ex = client.post("/api/tools/execute", json={
        "server": "mockmcp", "tool": "echo", "args": {"text": "hi"}})
    assert ex.status_code == 200
    assert ex.json()["content"] == "hi"
    runs = client.get("/api/tools/runs").json()
    assert any(r["tool"] == "echo" for r in runs)
    tog = client.post("/api/tools/mockmcp/echo/toggle").json()
    assert tog["enabled"] is False


def test_chat_stream(llm_mock, authed):
    # self-sufficient: create provider, disable all MCP servers -> pure streaming path
    for s in client.get("/api/mcpservers").json():
        client.put(f"/api/mcpservers/{s['name']}", json={"enabled": False})
    r = client.post("/api/providers", json={
        "name": "chatllm", "dialect": "openai-chat", "baseURL": llm_mock,
        "model": "mock-model", "apiKey": "sk-test-123"})
    assert r.status_code == 200, r.text
    cid = None
    with client.stream("POST", "/api/chat", json={
        "message": "hello", "provider": "chatllm", "model": "mock-model"}) as resp:
        assert resp.status_code == 200
        events = []
        for line in resp.iter_lines():
            if line.startswith("event: "):
                events.append(line.split("event: ")[1])
            elif line.startswith("data: "):
                events.append(line.split("data: ")[1])
        text = "".join(json.loads(d)["text"] for d in events[1:] if d.startswith('{"type": "text"'))
        print("CHAT EVENTS:", events)
        assert text == "Hello world", events
        assert "done" in events
    convs = client.get("/api/conversations").json()
    assert convs, "no conversation persisted"
    cid = convs[0]["id"]
    msgs = client.get(f"/api/conversations/{cid}/messages").json()
    assert any(m["role"] == "user" and m["content"] == "hello" for m in msgs)
    assert any(m["role"] == "assistant" for m in msgs)


def test_chat_tool_loop(mcp_mock, authed):
    r = client.post("/api/mcpservers", json={
        "name": "loopmcp", "url": mcp_mock, "transport": "http"})
    assert r.status_code == 200, r.text
    with client.stream("POST", "/api/chat", json={
        "message": "use echo", "provider": "chatllm", "model": "mock-model"}) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())
        assert "tool_start" in body and ("max turns" in body or "done" in body)


def test_chat_requires_config(authed):
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 400


def test_files(authed):
    r = client.post("/api/files", files={"file": ("hello.txt", b"hello-content", "text/plain")})
    assert r.status_code == 200, r.text
    name = r.json()["name"]
    lst = client.get("/api/files").json()
    assert any(f["name"] == name for f in lst)
    dl = client.get(f"/api/files/{name}")
    assert dl.content == b"hello-content"
    assert client.delete(f"/api/files/{name}").status_code == 200


def test_audit_and_settings(authed):
    a = client.get("/api/audit").json()
    assert len(a) > 0
    r = client.put("/api/settings", json={"theme": "light"})
    assert r.status_code == 200
    assert client.get("/api/settings").json()["theme"] == "light"
