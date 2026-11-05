"""Agent loop: streaming provider completion + MCP tool execution with visibility events."""
import json
import re
import threading

import httpx

from . import mcp_client, providers

MAX_TURNS = 10
SSE_DATA_RE = re.compile(r"^data:\s*(.*)$")


class StopRequested(Exception):
    pass


class Agent:
    def __init__(self, provider_cfg, model, system_prompt=None, temperature=0.7,
                 tool_servers=None, stop_event: threading.Event = None):
        self.provider_cfg = provider_cfg
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.tool_servers = tool_servers or []
        self.stop_event = stop_event or threading.Event()
        self._server_clients = []

    def _check_stop(self):
        if self.stop_event.is_set():
            raise StopRequested()

    def _load_tools(self):
        tools = []
        self._server_clients = []
        for s in self.tool_servers:
            self._check_stop()
            try:
                client = mcp_client.MCPClient(s["url"], s.get("headers"), s.get("transport", "http"))
                client.initialize()
                tlist = client.tools_list()
            except Exception:
                continue
            self._server_clients.append((s["name"], client))
            for t in tlist:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"{s['name']}__{t.get('name')}",
                        "description": t.get("description", ""),
                        "parameters": t.get("inputSchema") or {"type": "object", "properties": {}},
                    },
                })
        return tools

    def _execute_tool(self, full_name, args):
        server_name, sep, tool_name = full_name.partition("__")
        if not sep:
            server_name, tool_name = "", full_name
        for sname, client in self._server_clients:
            if sname == server_name:
                try:
                    result = client.call_tool(tool_name, args)
                except Exception as e:
                    result = {"isError": True, "content": f"{type(e).__name__}: {e}"}
                return {"server": server_name, "tool": tool_name, "result": result}
        return {"server": server_name, "tool": tool_name,
                "result": {"isError": True, "content": "tool not found"}}

    def run(self, history):
        """history: list of {"role","content"}. Yields event dicts."""
        try:
            yield {"type": "agent_start"}
            tools = self._load_tools()
            yield {"type": "tools_loaded", "count": len(tools)}
            messages = list(history)
            done = False
            for turn in range(MAX_TURNS):
                self._check_stop()
                text, tool_calls, events = self._stream_once(messages, tools)
                for ev in events:
                    yield ev
                messages.append({"role": "assistant", "content": text or None,
                                 "tool_calls": tool_calls or None})
                if not tool_calls:
                    done = True
                    break
                for tc in tool_calls:
                    self._check_stop()
                    name = tc["function"]["name"]
                    args = tc["function"].get("arguments", {})
                    yield {"type": "tool_start", "name": name, "args": args}
                    res = self._execute_tool(name, args)
                    yield {"type": "tool_end", "name": name, "result": res}
                    messages.append({"role": "tool", "tool_call_id": tc["id"],
                                     "content": res["result"]["content"] or "(empty)"})
            if done:
                yield {"type": "done"}
            else:
                yield {"type": "error", "text": "max turns reached"}
        except StopRequested:
            yield {"type": "stopped"}
        except Exception as e:
            import traceback
            yield {"type": "error", "text": f"{type(e).__name__}: {e}",
                   "trace": traceback.format_exc()[-1500:]}

    def _stream_once(self, messages, tools_spec):
        """Stream one completion; returns (text, tool_calls_list_or_None, events)."""
        url = f"{providers._base(self.provider_cfg)}/chat/completions"
        body = {
            "model": self.model,
            "messages": providers._chat_messages(messages, self.system_prompt),
            "temperature": float(self.temperature),
            "stream": True,
        }
        if tools_spec:
            body["tools"] = tools_spec
        events = []
        text_parts = []
        tool_calls = {}
        try:
            with httpx.Client(timeout=providers.DEFAULT_TIMEOUT,
                              headers=providers._headers(self.provider_cfg)) as client:
                with client.stream("POST", url, json=body) as resp:
                    if resp.status_code >= 400:
                        err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                        events.append({"type": "error", "text": err})
                        return "".join(text_parts), None, events
                    for line in resp.iter_lines():
                        self._check_stop()
                        line = line.strip()
                        m = SSE_DATA_RE.match(line)
                        if not m:
                            continue
                        payload = m.group(1).strip()
                        if payload == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        for choice in chunk.get("choices", []):
                            delta = choice.get("delta") or {}
                            if delta.get("content"):
                                text_parts.append(delta["content"])
                                events.append({"type": "text", "text": delta["content"]})
                            for tc in delta.get("tool_calls") or []:
                                idx = tc.get("index", 0)
                                slot = tool_calls.setdefault(idx, {
                                    "id": None, "type": "function",
                                    "function": {"name": "", "arguments": ""}})
                                if tc.get("id"):
                                    slot["id"] = tc["id"]
                                fn = tc.get("function") or {}
                                if fn.get("name"):
                                    slot["function"]["name"] += fn["name"]
                                if fn.get("arguments") is not None:
                                    slot["function"]["arguments"] += fn["arguments"]
        except httpx.HTTPError as e:
            events.append({"type": "error", "text": f"connection error: {e}"})
        except StopRequested:
            raise

        text = "".join(text_parts)
        if tool_calls:
            calls = []
            for _, slot in sorted(tool_calls.items()):
                if not slot["function"]["name"]:
                    continue
                slot["function"]["arguments"] = _safe_json(slot["function"]["arguments"])
                slot["id"] = slot["id"] or f"call_{len(calls)}"
                calls.append(slot)
            return text, calls or None, events
        return text, None, events


def _safe_json(s):
    try:
        return json.loads(s) if s else {}
    except Exception:
        return {}
