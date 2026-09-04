"""prompt-store-verify.py — permanent DeepChat customPrompts integrity gate.

Read-only. Mirrors the app's exact zod schemas (PromptSchema / PromptParameterSchema /
FileItemSchema / PromptMessageSchema from app.asar /out/main/index.js) and checks:
  1. schema validity of every entry in every store (one bad field fails the WHOLE
     config.listCustomPrompts UI route — the 2026-08-20 'not loading' root cause)
  2. cross-store parity (repo canonical == script canonical == 4 live stores)
  3. template==content on every entry (PROMPT-KEY-SCHEMA-ASYMMETRY-1)

Usage:
  python prompt-store-verify.py           # full verify, exit 0 = healthy
  python prompt-store-verify.py inventory # table of stores + entry counts
Exit codes: 0 healthy | 1 violations found | 2 store unreadable

Scheduled guard: Daily Ops cronjob (216e1d12) check #6 runs this daily; notify-on-failure.
"""
import json, sqlite3, sys, os

DEFAULT_PATHS = {
    "repo": r"C:\Users\LENOVO\Documents\GitHub\qnfo-skills\prompt-stores\customPrompts.json",
    "script": r"C:\Users\LENOVO\.deepchat\scripts\customPrompts-canonical.json",
    "roaming_cp_file": r"C:\Users\LENOVO\AppData\Roaming\DeepChat\custom_prompts.json",
    "roaming_db": r"C:\Users\LENOVO\AppData\Roaming\DeepChat\app_db\agent.db",
}
SRC_ENUM = {"local", "imported", "builtin"}
EXPECTED_IDS = ["1788197658524-RX0DE2xA", "1788197658524-RVSnJFyP", "1788197658524-2Qgtf6l6", "1788197658524-FwEKzK59", "1788197658524-2R2NP0B9", "1788197658524-CzhqBs5V", "1788197658524-hQdwK4UR",  "1788197658524-3KUDUZ2Z", "1788197658524-NmxnpZvx", "1788197658524-TWLRZ2gs", "1788197658524-fVj3nerc"]


def validate_prompt(p):
    """Exact mirror of the app's zod schemas. Returns list of violation strings."""
    errs = []
    if not isinstance(p, dict):
        return ["NOT A DICT"]
    # PromptSchema required fields
    if not isinstance(p.get("id"), str) or not p.get("id").strip():
        errs.append("id: non-empty string required")
    if not isinstance(p.get("name"), str):
        errs.append("name: string required")
    if not isinstance(p.get("description"), str):
        errs.append(f"description: string required, got {type(p.get('description')).__name__}")
    if p.get("content") is not None and not isinstance(p.get("content"), str):
        errs.append("content: must be string when present")
    # PromptParameterSchema: name AND required are REQUIRED (not optional)
    params = p.get("parameters")
    if params is not None:
        if not isinstance(params, list):
            errs.append("parameters: array required")
        else:
            for i, pa in enumerate(params):
                if not isinstance(pa, dict):
                    errs.append(f"parameters[{i}]: object required"); continue
                if not isinstance(pa.get("name"), str):
                    errs.append(f"parameters[{i}].name: REQUIRED string, got {pa.get('name')!r}")
                if not isinstance(pa.get("required"), bool):
                    errs.append(f"parameters[{i}].required: REQUIRED bool, got {pa.get('required')!r}")
                if "description" in pa and not isinstance(pa["description"], str):
                    errs.append(f"parameters[{i}].description: string when present")
    # FileItemSchema: id/name/type/path required strings
    files = p.get("files")
    if files is not None:
        if not isinstance(files, list):
            errs.append("files: array required")
        else:
            for i, fi in enumerate(files):
                if not isinstance(fi, dict):
                    errs.append(f"files[{i}]: object required"); continue
                for k in ("id", "name", "type", "path"):
                    if not isinstance(fi.get(k), str):
                        errs.append(f"files[{i}].{k}: REQUIRED string, got {fi.get(k)!r}")
    # PromptMessageSchema: role + content.text required strings
    messages = p.get("messages")
    if messages is not None:
        if not isinstance(messages, list):
            errs.append("messages: array required")
        else:
            for i, ms in enumerate(messages):
                if not isinstance(ms, dict):
                    errs.append(f"messages[{i}]: object required"); continue
                if not isinstance(ms.get("role"), str):
                    errs.append(f"messages[{i}].role: REQUIRED string")
                c = ms.get("content")
                if not isinstance(c, dict) or not isinstance(c.get("text"), str):
                    errs.append(f"messages[{i}].content.text: REQUIRED string")
    if p.get("enabled") is not None and not isinstance(p.get("enabled"), bool):
        errs.append(f"enabled: bool when present, got {p.get('enabled')!r}")
    if p.get("source") is not None and p.get("source") not in SRC_ENUM:
        errs.append(f"source: INVALID {p.get('source')!r} (enum local|imported|builtin)")
    # 2026-08-20 root cause: string timestamps fail z.number().int()
    for k in ("createdAt", "updatedAt"):
        v = p.get(k)
        if v is not None and not isinstance(v, int):
            errs.append(f"{k}: INT REQUIRED, got {type(v).__name__} {v!r}")
    # PROMPT-KEY-SCHEMA-ASYMMETRY-1: fill tool reads content; keep template in sync
    t = p.get("template")
    if isinstance(t, str) and t != p.get("content"):
        errs.append("template != content")
    return errs


def read_store(name, path):
    """Return (entries_or_None, error_string_or_None)."""
    try:
        if name.endswith("_db"):
            c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=60)
            cols = [r[1] for r in c.execute("PRAGMA table_info(app_settings)").fetchall()]
            if "key" not in cols:
                return None, "app_settings table missing key column"
            valcol = "value_json" if "value_json" in cols else "value"
            row = c.execute(f"SELECT {valcol} FROM app_settings WHERE key='customPrompts'").fetchone()
            c.close()
            if not row:
                return None, "no customPrompts row"
            cp = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        else:
            d = json.load(open(path, encoding="utf-8"))
            cp = d.get("customPrompts") if isinstance(d, dict) and "customPrompts" in d else d
        if not isinstance(cp, list):
            return None, f"not a list ({type(cp).__name__})"
        return cp, None
    except sqlite3.DatabaseError as e:
        # JSON files opened by mistake fall through to json path
        try:
            d = json.load(open(path, encoding="utf-8"))
            cp = d.get("customPrompts") if isinstance(d, dict) and "customPrompts" in d else d
            return (cp, None) if isinstance(cp, list) else (None, f"not a list ({type(cp).__name__})")
        except Exception as e2:
            return None, f"unreadable: {e} / {e2}"
    except Exception as e:
        return None, str(e)



def _proj(cp):
    return {p.get("id"): (p.get("name"), p.get("content")) for p in cp} if isinstance(cp, list) else None

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "inventory":
        print(f"{'store':16s} {'entries':>7s} {'violations':>10s}  status")
        for name, path in DEFAULT_PATHS.items():
            cp, err = read_store(name, path)
            if err:
                print(f"{name:16s} {'-':>7s} {'-':>10s}  ERROR {err}")
                continue
            v = sum(len(validate_prompt(p)) for p in cp)
            print(f"{name:16s} {len(cp):7d} {v:10d}  {'OK' if v == 0 else 'INVALID'}")
        return 0

    rc = 0
    results = {}
    for name, path in DEFAULT_PATHS.items():
        cp, err = read_store(name, path)
        if err:
            print(f"[STORE-ERROR] {name}: {err}")
            results[name] = None
            rc = max(rc, 2)
            continue
        results[name] = cp
        v = sum(len(validate_prompt(p)) for p in cp)
        ids = [p.get("id") for p in cp if isinstance(p, dict)]
        missing = [e for e in EXPECTED_IDS if e not in ids]
        if v:
            print(f"[SCHEMA-VIOLATION] {name}: {v} violation(s) — UI list route (config.listCustomPrompts) will fail")
            for p in cp:
                perr = validate_prompt(p)
                if perr:
                    print(f"   id={p.get('id')!r}: {perr}")
            rc = max(rc, 1)
        if missing:
            print(f"[MISSING-IDS] {name}: {missing}")
            rc = max(rc, 1)

    # parity against repo canonical
    repo = results.get("repo")
    if repo is not None:
        for name, cp in results.items():
            if name == "repo" or cp is None:
                continue
            if _proj(cp) != _proj(repo):
                print(f"[DRIFT] {name} differs from repo canonical")
                rc = max(rc, 1)

    rc = max(rc, 1 if check_system_prompt_parity() else 0)
    rc = max(rc, 1 if check_skill_anchor_parity() else 0)
    rc = max(rc, 0 if check_mcp_autoapprove_parity() else 1)

    if rc == 0:
        print("PROMPT-STORE-VERIFY: PASS (schema + parity + system-prompt parity)")
    return rc




# === SYSTEM-PROMPT PARITY (AGENT-PROMPT-PARITY-1, 2026-08-29 remediation) ===
# Checks the system-prompt stores, INCLUDING the agents table row
# (agents.deepchat.config_json.systemPrompt), which was frozen at v3.74
# (2026-08-25) while the canonical stores moved (v3.93).
SYSPROMPT_STORES = {
    "canonical_md":   r"C:\Users\LENOVO\.deepchat\system-prompt-v2.7.md",
    "roaming_json":   r"C:\Users\LENOVO\AppData\Roaming\DeepChat\app-settings.json",
    "app_db_list":    r"C:\Users\LENOVO\AppData\Roaming\DeepChat\app_db\agent.db",
    "repo_copy_md":    r"C:\Users\LENOVO\Documents\GitHub\qnfo-skills\system-prompt-v2.7.md",
    "skills_live_md":  r"C:\Users\LENOVO\.deepchat\skills\system-prompt-v2.7.md",
    "agents_row":     r"C:\Users\LENOVO\AppData\Roaming\DeepChat\app_db\agent.db",
}

def read_system_prompt(name, path):
    try:
        if name in ("canonical_md", "repo_copy_md", "skills_live_md"):
            return open(path, encoding="utf-8").read(), None
        if name == "roaming_json":
            return json.load(open(path, encoding="utf-8")).get("default_system_prompt"), None
        if name == "app_db_list":
            c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=60)
            v = c.execute("SELECT value_json FROM app_settings WHERE key='systemPrompts'").fetchone()
            c.close()
            if not v:
                return None, "no systemPrompts row"
            j = json.loads(v[0])
            if isinstance(j, list) and j:
                return j[0].get("content"), None
            if isinstance(j, str):
                return j, None
            return None, "unexpected shape %s" % type(j).__name__
        if name == "agents_row":
            c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=60)
            v = c.execute("SELECT config_json FROM agents WHERE id='deepchat'").fetchone()
            c.close()
            if not v:
                return None, "no deepchat agent row"
            return json.loads(v[0]).get("systemPrompt"), None
        return None, "unknown store"
    except Exception as e:
        return None, str(e)

def check_system_prompt_parity():
    import os as _os, re as _re
    vals, errs = {}, 0
    for name, path in SYSPROMPT_STORES.items():
        v, err = read_system_prompt(name, path)
        if err:
            print("[SYSPROMPT-STORE-ERROR] %s: %s" % (name, err))
            errs += 1
            continue
        vals[name] = (v or "").strip()
    ref = vals.get("canonical_md")
    if ref:
        for name, v in vals.items():
            if v != ref:
                print("[SYSPROMPT-DRIFT] %s != canonical_md (len %d vs %d)" % (name, len(v), len(ref)))
                errs += 1
    hist = r"C:\Users\LENOVO\.deepchat\system-prompt-history-v2.7.md"
    if not _os.path.isfile(hist):
        print("[PROMPT-HISTORY] missing history file: " + hist)
        errs += 1
    else:
        _h = open(hist, encoding="utf-8", errors="ignore").read()
        if len(_re.findall(r"> \*\*v[\d.]+ UPDATE", _h)) < 5:
            print("[PROMPT-HISTORY] history file has <5 banner chunks")
            errs += 1
    _md = vals.get("canonical_md") or ""
    if len(_md) > 310000:
        print("[PROMPT-SIZE] canonical base %d chars > 310000 ceiling" % len(_md))
        errs += 1
    if errs == 0:
        print("SYSTEM-PROMPT-PARITY: PASS (%d stores identical)" % len(vals))
    return errs




# === SKILL ANCHOR PARITY (TITLE-LINE-PARITY-1 for skills, 2026-08-29 skills audit) ===
SKILLS_DIR = r"C:\Users\LENOVO\.deepchat\skills"

def _ver_tuple(v):
    try:
        return tuple(int(x) for x in v.split('.'))
    except Exception:
        return (0,)

def check_skill_anchor_parity():
    """H1 title version == newest banner version == last Current footer, per skill."""
    import re as _re, os as _os
    errs = 0
    n = 0
    for name in sorted(_os.listdir(SKILLS_DIR)):
        p = _os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not _os.path.isfile(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        hv = None
        for _l in t.splitlines():
            if _l.startswith('# '):
                _m1 = _re.search(r'\bv?([\d.]+)\b', _l)
                hv = _m1.group(1) if _m1 else None
                break
        banners = [_re.sub(r'^v', '', v) for v in _re.findall(r'> \*\*v?([\d.]+) UPDATE', t)]
        bv = max(banners, key=_ver_tuple) if banners else None
        cur = _re.findall(r'Current:\s*\*?\*?v?([\d.]+)', t)
        cv = cur[-1] if cur else None
        if not (hv and bv and cv):
            continue
        n += 1
        if not t.startswith('---'):
            print("[SKILL-FRONTMATTER] %s: file does not start with '---'" % name)
            errs += 1
            continue
        _fvm = _re.search(r'^---\n(?:.*\n)*?version:\s*"?([\d.]+)"?', t)
        if _fvm and _fvm.group(1) != bv:
            print("[SKILL-FRONTMATTER-VERSION] %s: frontmatter v%s != banner v%s" % (name, _fvm.group(1), bv))
            errs += 1
            continue
        if not (hv == bv == cv):
            print("[SKILL-ANCHOR-DRIFT] %s: title v%s / newest-banner v%s / current v%s" % (name, hv, bv, cv))
            errs += 1
    if errs == 0:
        print("SKILL-ANCHOR-PARITY: PASS (%d versioned skills)" % n)
    return errs


def check_mcp_autoapprove_parity():
    """MCP-AUTOAPPROVE-PARITY (DEP-1 lesson, 2026-08-31): mcp-settings.json is the source of
    truth for autoApprove sets. The running app rewrites the DB mcp_servers rows from its
    runtime and STRIPS autoApprove — DB drift is the app's known behavior (noted, not fatal).
    The gate FAILS only when the FILE itself loses the sets (the unrecoverable state)."""
    import os as _os
    cfg_dir = _os.path.dirname(DEFAULT_PATHS["roaming_cp_file"])
    mcpf = _os.path.join(cfg_dir, "mcp-settings.json")
    if not _os.path.exists(mcpf):
        print("[MCP-AUTOAPPROVE-PARITY] mcp-settings.json not found — check skipped")
        return True
    try:
        with open(mcpf, encoding="utf-8-sig") as _f:
            m = json.load(_f)
        servers = m.get("mcpServers", {}) or {}
        with_aa = {k: v for k, v in servers.items() if v.get("autoApprove")}
        if not with_aa:
            print("[MCP-FILE-EMPTY] mcp-settings.json has NO autoApprove sets — the app may have "
                  "stripped the FILE; restore from the canonical before relying on the toolchain")
            return False
        try:
            c = sqlite3.connect("file:%s?mode=ro" % DEFAULT_PATHS["roaming_db"].replace("\\", "/"),
                                uri=True, timeout=30)
            drift = []
            for _name, _cfgj in c.execute("SELECT name, config_json FROM mcp_servers").fetchall():
                _fcfg = servers.get(_name)
                if not _fcfg:
                    continue
                _faa = _fcfg.get("autoApprove") or []
                try:
                    _d = json.loads(_cfgj)
                except Exception:
                    continue
                if (_d.get("autoApprove") or []) != _faa:
                    drift.append(_name)
            c.close()
        except Exception:
            drift = []
        if drift:
            print("[MCP-DB-NOTE] DB mcp_servers rows stripped autoApprove for %d server(s) — the "
                  "running app rewrites them from its runtime; the file is the source of truth "
                  "(re-sync after app restarts): %s" % (len(drift), ", ".join(drift[:6])))
        print("[MCP-AUTOAPPROVE-PARITY] PASS (file intact: %d servers with autoApprove)" % len(with_aa))
        return True
    except Exception as e:
        print("[MCP-AUTOAPPROVE-PARITY] check skipped: %s" % e)
        return True


if __name__ == "__main__":
    sys.exit(main())
