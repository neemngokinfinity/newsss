"""Minimal MCP client over HTTP (JSON-RPC 2.0, streamable-HTTP style POST).

Only transports that are actually implemented here are supported:
- 'http': POST JSON-RPC messages to <url> (works with many streamable-HTTP servers
  and with simple JSON-RPC MCP endpoints). Responses may be JSON or SSE-framed.
Any other transport (stdio, original SSE) raises NotImplementedError so the UI
never advertises support it doesn't have.
"""
import json
import uuid

import httpx

DEFAULT_TIMEOUT = 20.0


class MCPError(Exception):
    pass


class UnsupportedTransport(MCPError):
    pass


class MCPClient:
    def __init__(self, url, headers=None, transport="http", timeout=DEFAULT_TIMEOUT):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.transport = transport
        self.timeout = timeout
        self._id = 0
        self.session_id = None
        self.capabilities = None
        if transport not in ("http",):
            raise UnsupportedTransport(
                f"transport '{transport}' is not implemented by this platform (only 'http' POST)"
            )

    def _request(self, method, params):
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        headers = {"Content-Type": "application/json", **self.headers}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        with httpx.Client(timeout=self.timeout, headers=headers) as client:
            resp = client.post(self.url, content=json.dumps(payload))
        if resp.status_code >= 400:
            raise MCPError(f"HTTP {resp.status_code}: {(resp.text or '')[:300]}")
        data = self._parse_body(resp)
        if isinstance(data, list):
            # streamable-HTTP may return a batch; take the one matching our id
            data = next((d for d in data if isinstance(d, dict) and d.get("id") == self._id), data[0])
        if not isinstance(data, dict):
            raise MCPError("non-JSON response from MCP server")
        if "result" in data:
            return data["result"]
        if "error" in data:
            err = data["error"]
            raise MCPError(f"MCP error {err.get('code')}: {err.get('message')}")
        raise MCPError("unknown JSON-RPC response")

    def _parse_body(self, resp):
        ctype = resp.headers.get("content-type", "")
        if "text/event-stream" in ctype:
            for line in resp.text.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        continue
            raise MCPError("empty SSE stream")
        try:
            return resp.json()
        except json.JSONDecodeError:
            raise MCPError("non-JSON response from MCP server")

    def initialize(self):
        result = self._request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "nanobot-platform", "version": "0.1.0"},
        })
        self.capabilities = result.get("capabilities") or {}
        sid = (result.get("_meta") or {}).get("sessionId")
        if sid:
            self.session_id = sid
        try:
            self._request("notifications/initialized", {})
        except Exception:
            pass
        return result

    def tools_list(self):
        result = self._request("tools/list", {})
        return result.get("tools", [])

    def call_tool(self, name, args):
        try:
            result = self._request("tools/call", {"name": name, "arguments": args or {}})
        except MCPError:
            raise
        content = []
        is_error = False
        if isinstance(result, dict):
            is_error = bool(result.get("isError"))
            for item in result.get("content", []):
                if item.get("type") == "text":
                    content.append(item.get("text", ""))
                elif item.get("type") == "image":
                    content.append("[image]")
                else:
                    content.append(json.dumps(item, ensure_ascii=False))
        return {"isError": is_error, "content": "\n".join(content)}
