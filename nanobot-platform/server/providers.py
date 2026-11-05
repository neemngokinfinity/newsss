"""LLM provider calls (OpenAI-compatible dialects).

Implemented dialects (honest subset):
- openai-chat: POST {base}/chat/completions, streaming SSE supported.
- openai-responses: POST {base}/responses (non-streaming only for now).
- generic-openresponses: same as openai-responses but at any baseURL.
Anything else raises ProviderNotImplemented so the UI shows the limitation clearly.
"""
import json
import re

import httpx

DEFAULT_TIMEOUT = 60.0
SSE_DATA_RE = re.compile(r"^data:\s*(.*)$")


class ProviderError(Exception):
    pass


class ProviderNotImplemented(ProviderError):
    pass


DIALECTS = {
    "openai-chat": ("chat", True),
    "openai-responses": ("responses", False),
    "generic-openresponses": ("responses", False),
}


def _resolve_key(provider):
    key = provider.get("apiKey") or ""
    m = re.match(r"^\${([A-Za-z_][A-Za-z0-9_]*)}$", str(key))
    if m:
        import os
        return os.environ.get(m.group(1), "")
    return str(key)


def _headers(provider):
    return {"Authorization": f"Bearer {_resolve_key(provider)}", ** (provider.get("headers") or {})}


def test_provider(provider):
    """Liveness check: GET {base}/models (widely supported by OpenAI-compatible APIs)."""
    base = (provider.get("baseURL") or "").rstrip("/")
    if not base:
        raise ProviderError("baseURL is required")
    try:
        with httpx.Client(timeout=15, headers=_headers(provider)) as client:
            r = client.get(f"{base}/models")
        if r.status_code in (200, 201):
            return {"ok": True, "detail": "connected"}
        return {"ok": False, "detail": f"HTTP {r.status_code}: {(r.text or '')[:200]}"}
    except httpx.HTTPError as e:
        return {"ok": False, "detail": f"connection error: {e}"}


def _base(provider):
    return (provider.get("baseURL") or "").rstrip("/")


def _chat_messages(messages, system_prompt=None):
    out = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})
    for m in messages:
        out.append({"role": m["role"], "content": m.get("content", "")})
    return out


def stream_chat(provider, model, messages, temperature=0.7, system_prompt=None):
    """Yield event dicts: {"type":"text","text":...} | {"type":"done"} | {"type":"error","text":...}"""
    dialect, can_stream = DIALECTS.get(provider.get("dialect", "OpenAIResponses"), (None, False))
    if dialect is None:
        yield {"type": "error", "text": f"dialect '{provider.get('dialect')}' not implemented"}
        return
    if dialect == "chat":
        yield from _chat_completions(provider, model, messages, temperature, system_prompt)
    else:
        yield from _responses(provider, model, messages, system_prompt)


def _chat_completions(provider, model, messages, temperature, system_prompt, stream=True):
    url = f"{_base(provider)}/chat/completions"
    body = {
        "model": model,
        "messages": _chat_messages(messages, system_prompt),
        "temperature": float(temperature),
    }
    if stream:
        body["stream"] = True
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT, headers=_headers(provider)) as client:
            if stream:
                with client.stream("POST", url, json=body) as resp:
                    if resp.status_code >= 400:
                        yield {"type": "error", "text": f"HTTP {resp.status_code}: {resp.text[:300]}"}
                        return
                    for line in resp.iter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        for choice in chunk.get("choices", []):
                            delta = choice.get("delta") or {}
                            if delta.get("content"):
                                yield {"type": "text", "text": delta["content"]}
                yield {"type": "done"}
            else:
                r = client.post(url, json=body)
                if r.status_code >= 400:
                    yield {"type": "error", "text": f"HTTP {r.status_code}: {r.text[:300]}"}
                    return
                data = r.json()
                for choice in data.get("choices", []):
                    if choice.get("message", {}).get("content"):
                        yield {"type": "text", "text": choice["message"]["content"]}
                yield {"type": "done"}
    except httpx.HTTPError as e:
        yield {"type": "error", "text": f"connection error: {e}"}


def _responses(provider, model, messages, system_prompt):
    url = f"{_base(provider)}/responses"
    body = {
        "model": model,
        "input": _chat_messages(messages, system_prompt),
    }
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT, headers=_headers(provider)) as client:
            r = client.post(url, json=body)
            if r.status_code >= 400:
                yield {"type": "error", "text": f"HTTP {r.status_code}: {r.text[:300]}"}
                return
            data = r.json()
            out = []
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            out.append(c.get("text", ""))
            yield {"type": "text", "text": "".join(out)}
            yield {"type": "done"}
    except httpx.HTTPError as e:
        yield {"type": "error", "text": f"connection error: {e}"}
