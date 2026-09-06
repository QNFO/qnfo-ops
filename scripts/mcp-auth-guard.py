#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp-auth-guard.py v1.0 — Cloudflare MCP header-auth watchdog (2026-08-20).

Why: remote Cloudflare MCP servers (mcp.cloudflare.com family) connect via
`mcp-remote` with OAuth-auto. OAuth token caches under ~/.mcp-auth get wiped
or expire (canonical: cloudflare-graphql "Couldn't connect" 2026-08-20;
cloudflare-observability/radar removed 2026-08-17 for "no cached OAuth
tokens"). Root fix: all 6 OAuth Cloudflare servers now use a long-lived API
token via `--header "Authorization: Bearer <token>"` — no OAuth dependency.

This guard verifies BOTH config stores carry the header auth for all 6
servers and AUTO-REPAIRS them if a regression (UI edit, restore, sync)
removes it. Wired into the cf_audit_hook SessionStart event.

Stores:
  1. %APPDATA%/DeepChat/mcp-settings.json -> mcpServers.<name>.args
  2. %APPDATA%/DeepChat/app_db/agent.db    -> mcp_servers.config_json

Token source: %USERPROFILE%/tokens/cloudflare  (cfat_...)

Stdlib only. Fast (<1s). Always exits 0 (never disrupts the app).
Usage: python mcp-auth-guard.py [--check-only]
"""
import json
import os
import sqlite3
import sys
import time

APP = os.path.join(os.environ.get("APPDATA", ""), "DeepChat")
TOKEN_FILE = os.path.join(os.environ.get("USERPROFILE", ""), "tokens", "cloudflare")
MCP_SETTINGS = os.path.join(APP, "mcp-settings.json")
AGENT_DB = os.path.join(APP, "app_db", "agent.db")

TARGETS = [
    "cloudflare",
    "cloudflare-bindings",
    "cloudflare-builds",
    "cloudflare-ai-gateway",
    "cloudflare-graphql",
    "cloudflare-auditlogs",
]
URL_SUFFIX = "mcp.cloudflare.com/mcp"


def get_token():
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            tok = f.read().strip()
        return tok if tok.startswith("cfat_") else None
    except OSError:
        return None


def header_args(url, token):
    return ["-y", "mcp-remote", "--header", "Authorization: Bearer " + token, url]


def check_args(args, token):
    return (
        isinstance(args, list)
        and len(args) >= 5
        and "--header" in args
        and any(token in u for u in args if isinstance(u, str))
        and any(u.endswith(URL_SUFFIX) for u in args if isinstance(u, str))
    )


def guard_json_settings(token, check_only=False):
    """Store 1: %APPDATA%/DeepChat/mcp-settings.json"""
    if not os.path.exists(MCP_SETTINGS):
        return "skip(missing)"
    with open(MCP_SETTINGS, "r", encoding="utf-8") as f:
        data = json.load(f)
    servers = data.get("mcpServers", {})
    repaired = []
    for name in TARGETS:
        s = servers.get(name)
        if not s:
            continue
        args = s.get("args") or []
        url = next((u for u in args if isinstance(u, str) and u.endswith(URL_SUFFIX)), None)
        if url and not check_args(args, token):
            if check_only:
                return "FAIL(" + name + ")"
            s["args"] = header_args(url, token)
            repaired.append(name)
    if repaired:
        bak = MCP_SETTINGS + ".bak-mcp-guard-" + time.strftime("%Y%m%d-%H%M%S")
        try:
            os.replace(MCP_SETTINGS, bak)
        except OSError:
            pass
        with open(MCP_SETTINGS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent="\t")
        return "REPAIRED:" + ",".join(repaired)
    return "PASS"


def guard_agent_db(token, check_only=False):
    """Store 2: %APPDATA%/DeepChat/app_db/agent.db -> mcp_servers.config_json"""
    if not os.path.exists(AGENT_DB):
        return "skip(missing)"
    repaired = []
    try:
        con = sqlite3.connect(AGENT_DB, timeout=5)
        con.execute("PRAGMA busy_timeout=5000")
        rows = list(con.execute("SELECT name, config_json FROM mcp_servers"))
        for name, val in rows:
            if name not in TARGETS:
                continue
            cfg = json.loads(val)
            args = cfg.get("args") or []
            url = next((u for u in args if isinstance(u, str) and u.endswith(URL_SUFFIX)), None)
            if url and not check_args(args, token):
                if check_only:
                    con.close()
                    return "FAIL(" + name + ")"
                cfg["args"] = header_args(url, token)
                cfg["configGeneration"] = cfg.get("configGeneration", 1) + 1
                con.execute(
                    "UPDATE mcp_servers SET config_json=?, updated_at=? WHERE name=?",
                    (json.dumps(cfg, ensure_ascii=False), int(time.time() * 1000), name),
                )
                repaired.append(name)
        con.commit()
        con.close()
    except Exception as e:  # never raise out of the hook
        return "ERR:" + str(e)[:80]
    return "REPAIRED:" + ",".join(repaired) if repaired else "PASS"


def main():
    check_only = "--check-only" in sys.argv
    token = get_token()
    if not token:
        print("[mcp-auth-guard] FAIL token-missing (%s)" % TOKEN_FILE)
        sys.exit(0)  # hook discipline: never non-zero
    out = {}
    out["json"] = guard_json_settings(token, check_only)
    out["db"] = guard_agent_db(token, check_only)
    print("[mcp-auth-guard] json=%s db=%s token=ok" % (out["json"], out["db"]))
    sys.exit(0)


if __name__ == "__main__":
    main()
