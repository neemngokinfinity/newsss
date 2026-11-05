"""nanobot-style YAML configuration manager (providers, MCP servers, agents)."""
import re
from pathlib import Path

import yaml

from . import db, settings

_ENV_REF = re.compile(r"^\${([A-Za-z_][A-Za-z0-9_]*)}$")
_MASK = "•••"


def ensure_defaults():
    settings.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    settings.AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.NANOBOT_YAML.exists():
        default = {"llmProviders": {}, "mcpServers": {}}
        save_yaml(settings.NANOBOT_YAML, default)
    if not (settings.AGENTS_DIR / "main.md").exists():
        (settings.AGENTS_DIR / "main.md").write_text(
            "---\nname: Main Assistant\ndescription: Default general-purpose agent\n"
            "model: \nprovider: \ntemperature: 0.7\nmcpServers: []\n---\n\n"
            "You are a helpful assistant.\n",
            encoding="utf-8",
        )
    try:
        os.chmod(settings.NANOBOT_YAML, 0o600)
    except Exception:
        pass


def load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def _mask_key(value):
    if value is None:
        return None
    m = _ENV_REF.match(str(value))
    if m:
        return {"env": m.group(1)}
    if str(value).strip():
        return {"env": None, "masked": _MASK}
    return None


# ---- providers ------------------------------------------------------------

def list_providers():
    cfg = load_yaml(settings.NANOBOT_YAML)
    out = []
    for name, p in (cfg.get("llmProviders") or {}).items():
        out.append({
            "name": name,
            "dialect": p.get("dialect", "OpenAIResponses"),
            "baseURL": p.get("baseURL", ""),
            "model": p.get("model", ""),
            "apiKey": _mask_key(p.get("apiKey")),
            "hasKey": p.get("apiKey") not in (None, ""),
            "extraHeaders": p.get("headers") or {},
        })
    return out


def upsert_provider(name, data):
    cfg = load_yaml(settings.NANOBOT_YAML)
    providers = cfg.setdefault("llmProviders", {})
    entry = dict(providers.get(name) or {})
    if "dialect" in data:
        entry["dialect"] = data["dialect"]
    if "baseURL" in data:
        entry["baseURL"] = data["baseURL"]
    if "model" in data:
        entry["model"] = data["model"]
    if "headers" in data:
        entry["headers"] = data["headers"] or {}
    if "apiKey" in data and data["apiKey"]:
        # accept either a literal key or ${ENV_VAR} reference
        entry["apiKey"] = data["apiKey"]
    providers[name] = entry
    save_yaml(settings.NANOBOT_YAML, cfg)
    db.audit("user", "provider_upsert", {"name": name})
    return {"name": name, **{k: v for k, v in entry.items() if k != "apiKey"},
            "hasKey": entry.get("apiKey") not in (None, "")}


def delete_provider(name):
    cfg = load_yaml(settings.NANOBOT_YAML)
    cfg.get("llmProviders", {}).pop(name, None)
    save_yaml(settings.NANOBOT_YAML, cfg)
    db.audit("user", "provider_delete", {"name": name})


def get_provider(name):
    cfg = load_yaml(settings.NANOBOT_YAML)
    return (cfg.get("llmProviders") or {}).get(name)


# ---- MCP servers ----------------------------------------------------------

def list_mcp_servers():
    cfg = load_yaml(settings.NANOBOT_YAML)
    out = []
    for name, s in (cfg.get("mcpServers") or {}).items():
        out.append({
            "name": name,
            "url": s.get("url", ""),
            "transport": s.get("transport", "http"),
            "headers": s.get("headers") or {},
            "enabled": s.get("enabled", True),
        })
    return out


def upsert_mcp_server(name, data):
    cfg = load_yaml(settings.NANOBOT_YAML)
    servers = cfg.setdefault("mcpServers", {})
    entry = dict(servers.get(name) or {})
    if "url" in data:
        entry["url"] = data["url"]
    if "transport" in data:
        entry["transport"] = data["transport"]
    if "headers" in data:
        entry["headers"] = data["headers"] or {}
    if "enabled" in data:
        entry["enabled"] = bool(data["enabled"])
    servers[name] = entry
    save_yaml(settings.NANOBOT_YAML, cfg)
    db.audit("user", "mcp_upsert", {"name": name})
    return {"name": name, **entry}


def delete_mcp_server(name):
    cfg = load_yaml(settings.NANOBOT_YAML)
    cfg.get("mcpServers", {}).pop(name, None)
    save_yaml(settings.NANOBOT_YAML, cfg)
    db.audit("user", "mcp_delete", {"name": name})


def get_mcp_server(name):
    cfg = load_yaml(settings.NANOBOT_YAML)
    return (cfg.get("mcpServers") or {}).get(name)


# ---- agents ---------------------------------------------------------------

def _parse_agent_md(path: Path):
    text = path.read_text(encoding="utf-8")
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
            except Exception:
                fm = {}
            body = text[end + 4:].lstrip("\n")
    return fm, body


def list_agents():
    out = []
    if settings.AGENTS_DIR.exists():
        for p in sorted(settings.AGENTS_DIR.glob("*.md")):
            fm, body = _parse_agent_md(p)
            out.append({
                "name": p.stem,
                "title": fm.get("name", p.stem),
                "description": fm.get("description", ""),
                "model": fm.get("model", ""),
                "provider": fm.get("provider", ""),
                "temperature": fm.get("temperature", 0.7),
                "mcpServers": fm.get("mcpServers", []),
                "tools": fm.get("tools") or [],
                "body": body[:4000],
            })
    return out


def get_agent(name):
    p = settings.AGENTS_DIR / f"{name}.md"
    if not p.exists():
        return None
    fm, body = _parse_agent_md(p)
    return {"name": name, **fm, "body": body}


def save_agent(name, data):
    fm = {
        "name": data.get("title") or name,
        "description": data.get("description", ""),
        "model": data.get("model", ""),
        "provider": data.get("provider", ""),
        "temperature": float(data.get("temperature", 0.7)),
        "mcpServers": data.get("mcpServers") or [],
        "tools": data.get("tools") or [],
    }
    body = data.get("body", "")
    text = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n\n" + body.strip() + "\n"
    (settings.AGENTS_DIR / f"{name}.md").write_text(text, encoding="utf-8")
    db.audit("user", "agent_save", {"name": name})


def delete_agent(name):
    p = settings.AGENTS_DIR / f"{name}.md"
    if p.exists():
        p.unlink()
        db.audit("user", "agent_delete", {"name": name})
