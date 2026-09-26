#!/usr/bin/env python3
"""model_guard.py v3 - OPS-SETTINGS-IMMUTABLE-1 permanent drift guard (2026-09-09).
HARDEN-AND-MANDATE (user directive 2026-09-09, applied systemwide): the canonical ops-exec
settings below are IMMUTABLE - no agent, session, or process may change them:
  model key        : QNFO-OPS / ops-frontier (GPT-5 frontier, tool_calls-capable) in ALL four DeepChat keys (DB + JSON)
  context window   : 1048576 (1M)   [DeepSeek source-truth ceiling]
  max output       : 393216 (384K)  [live probe valid range [1,393216]; 384000 accepted,
                                     500000 -> 400 invalid_request_error; MAX-OUT-393K-1]
  timeout (client) : 3600000 (1h)   [DeepChat model_configs]
  tool-loop        : 300s soft      [worker OPS_LOOP_DEADLINE_MS = cpu ceiling]
  workflow step    : 15 min         [Cloudflare Workflows max]
Covers DeepChat (agent.db model_configs + app_settings + app-settings.json), ChatBox
(xyz.chatboxapp.app/config.json qnfo-ops provider), and ANY future ops-endpoint client
(auto-discovered under %APPDATA% that references qnfo-ops.q08.workers.dev - SANNABOT is not
present as of 2026-09-09; when it appears, this guard adopts it automatically).

Canonical: QNFO/qnfo-ops/scripts/model_guard.py (mirror C:/Users/LENOVO/.deepchat/scripts).
Trigger: Windows Task Scheduler 'QNFO-ModelKey-Guard' every 30 min.
Recurrence-ZERO-1 guard for MODEL-KEY-FILE-DRIFT-1 + model-parameter drift.
Exit codes: 0=clean/fixed 1=check-error 2=failed-to-fix. Idempotent; silent when clean.
"""
import json, os, sqlite3, sys, tempfile, datetime, time

APP_DIR = os.path.expandvars(r"%APPDATA%\DeepChat")
DB = os.path.join(APP_DIR, "app_db", "agent.db")
JS = os.path.join(APP_DIR, "app-settings.json")
CHATBOX = os.path.expandvars(r"%APPDATA%\xyz.chatboxapp.app\config.json")
ROAM = os.path.expandvars(r"%APPDATA%")

DESIRED_KEY = {"providerId": "AI-GATEWAY", "modelId": "openai/gpt-4.1"}  # 2026-09-19 user directive: /ai/v1 universal gateway endpoint (openai/gpt-4.1), deprecate QNFO-OPS custom worker + Workers AI

# SESSION-DESIRED-KEY (2026-09-19 user directive): the per-SESSION executor is QNFO-OPS/ops-frontier --
# the fleet's SERVER-SIDE agent loop and the 'deepchat' agent-config value. DESIRED_KEY above is the
# app_settings PICKER default only; every session must run on a server-side executor (SERVER-SIDE-EXEC-100-1).
SESSION_KEY = {"providerId": "QNFO-OPS", "modelId": "ops"}
# parameter canon: DeepChat config_json keys (model_configs) + JSON contextWindow/maxOutput
CANON_PARAM = {
    "ops-exec": {"maxTokens": 393216, "contextLength": 1048576, "timeout": 3600000,
                 "contextWindow": 1048576, "maxOutput": 393216},
    "deepseek-v4-flash": {"maxTokens": 393216, "contextLength": 1048576, "timeout": 3600000,
                          "contextWindow": 1048576, "maxOutput": 393216},
    "ops": {"maxTokens": 393216, "contextLength": 1048576, "timeout": 600000,
             "contextWindow": 1048576, "maxOutput": 393216},
    "ops-frontier": {"maxTokens": 128000, "contextLength": 400000, "timeout": 600000,
                     "contextWindow": 400000, "maxOutput": 128000},
    "ops-frontier-mini": {"maxTokens": 128000, "contextLength": 400000, "timeout": 600000,
                          "contextWindow": 400000, "maxOutput": 128000},
    "ops-frontier-reason": {"maxTokens": 100000, "contextLength": 200000, "timeout": 600000,
                            "contextWindow": 200000, "maxOutput": 100000},
}

OPS_HOST_MARK = "qnfo-ops.q08.workers.dev"
OPS_HOST_MARK_NEW = "ops.qnfo.org"  # new bot-protection-bypass domain (2026-09-15)

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def ms():
    return int(time.time() * 1000)

def jload(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def atomic_json(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".mguard-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def norm_key(v):
    return v if isinstance(v, dict) else None

# ---------------- DeepChat DB ----------------
def dc_db_drift(c):
    drift = []
    for k in ("defaultModel", "preferredModel"):
        row = c.execute("SELECT value_json FROM app_settings WHERE key=?", (k,)).fetchone()
        if row is None:
            drift.append(k + ":missing"); continue
        try:
            v = json.loads(row[0])
        except Exception:
            drift.append(k + ":unparseable"); continue
        if v != DESIRED_KEY:
            drift.append(k + ":" + json.dumps(v))
    # model_configs params for QNFO-OPS models
    rows = c.execute("SELECT cache_key, config_json FROM model_configs WHERE provider_id='QNFO-OPS'").fetchall()
    for ck, cj in rows:
        mid = ck.split("-_-")[-1] if "-_-" in ck else ""
        want = CANON_PARAM.get(mid)
        if not want:
            continue
        try:
            obj = json.loads(cj)
        except Exception:
            drift.append(ck + ":unparseable"); continue
        cfg = obj.get("config") if isinstance(obj, dict) else None
        if not isinstance(cfg, dict):
            drift.append(ck + ":no-config"); continue
        for field, val in (("maxTokens", want["maxTokens"]), ("contextLength", want["contextLength"]), ("timeout", want["timeout"])):
            if cfg.get(field) != val:
                drift.append(ck + ":" + field + "=" + str(cfg.get(field)))
    return drift

def dc_db_fix(c):
    for k in ("defaultModel", "preferredModel"):
        c.execute("UPDATE app_settings SET value_json=?, updated_at=? WHERE key=?",
                  (json.dumps(DESIRED_KEY), now(), k))
    rows = c.execute("SELECT cache_key, config_json FROM model_configs WHERE provider_id='QNFO-OPS'").fetchall()
    for ck, cj in rows:
        mid = ck.split("-_-")[-1] if "-_-" in ck else ""
        want = CANON_PARAM.get(mid)
        if not want:
            continue
        try:
            obj = json.loads(cj)
        except Exception:
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("config"), dict):
            continue
        cfg = obj["config"]
        dirty = False
        for field, val in (("maxTokens", want["maxTokens"]), ("contextLength", want["contextLength"]), ("timeout", want["timeout"])):
            if cfg.get(field) != val:
                cfg[field] = val; dirty = True
        if dirty:
            c.execute("UPDATE model_configs SET config_json=?, updated_at=? WHERE cache_key=?",
                      (json.dumps(obj, ensure_ascii=False), ms(), ck))

# NON-TOOL-MODELS-1: pin functionCall=False for the server-side loop models (DeepChat agent flag).
def dc_functioncall_drift(c):
    drift = []
    rows = c.execute("SELECT cache_key, config_json FROM model_configs WHERE provider_id='QNFO-OPS'").fetchall()
    for ck, cj in rows:
        mid = ck.split("-_-")[-1] if "-_-" in ck else ""
        if mid not in NON_TOOL_MODELS:
            continue
        try:
            obj = json.loads(cj)
        except Exception:
            drift.append(ck + ":unparseable"); continue
        cfg = obj.get("config") if isinstance(obj, dict) else None
        if not isinstance(cfg, dict):
            drift.append(ck + ":no-config"); continue
        if cfg.get("functionCall") is not False:
            drift.append(ck + ":functionCall=" + str(cfg.get("functionCall")))
    return drift

def dc_functioncall_fix(c):
    rows = c.execute("SELECT cache_key, config_json FROM model_configs WHERE provider_id='QNFO-OPS'").fetchall()
    for ck, cj in rows:
        mid = ck.split("-_-")[-1] if "-_-" in ck else ""
        if mid not in NON_TOOL_MODELS:
            continue
        try:
            obj = json.loads(cj)
        except Exception:
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("config"), dict):
            continue
        if obj["config"].get("functionCall") is not False:
            obj["config"]["functionCall"] = False
            c.execute("UPDATE model_configs SET config_json=?, updated_at=? WHERE cache_key=?",
                      (json.dumps(obj, ensure_ascii=False), ms(), ck))

def dc_js_functioncall_drift(d):
    drift = []
    for pr in d.get("providers") or []:
        if (pr.get("id") or pr.get("providerId") or "") != "QNFO-OPS":
            continue
        for m in pr.get("models") or []:
            if (m.get("modelId") or m.get("id")) in NON_TOOL_MODELS and isinstance(m.get("capabilities"), list):
                if "tool_use" in m["capabilities"]:
                    drift.append("json:QNFO-OPS/" + str(m.get("modelId")) + ":capabilities has tool_use")
    return drift

def dc_js_functioncall_fix(d):
    for pr in d.get("providers") or []:
        if (pr.get("id") or pr.get("providerId") or "") != "QNFO-OPS":
            continue
        for m in pr.get("models") or []:
            if (m.get("modelId") or m.get("id")) in NON_TOOL_MODELS and isinstance(m.get("capabilities"), list):
                if "tool_use" in m["capabilities"]:
                    m["capabilities"] = [x for x in m["capabilities"] if x != "tool_use"]

# ---------------- DeepChat JSON ----------------
def dc_js_drift(d):
    drift = []
    for k in ("defaultModel", "preferredModel"):
        if d.get(k) != DESIRED_KEY:
            drift.append(k + ":" + json.dumps(d.get(k)))
    for pr in d.get("providers") or []:
        if (pr.get("id") or pr.get("providerId") or "") != "QNFO-OPS":
            continue
        for m in pr.get("models") or []:
            want = CANON_PARAM.get(m.get("id") or m.get("modelId"))
            if not want:
                continue
            for field, val in (("contextWindow", want["contextWindow"]), ("maxOutput", want["maxOutput"])):
                if m.get(field) != val:
                    drift.append("json:QNFO-OPS/" + str(m.get("id")) + ":" + field + "=" + str(m.get(field)))
    return drift

def dc_js_fix(d):
    for k in ("defaultModel", "preferredModel"):
        d[k] = DESIRED_KEY
    for pr in d.get("providers") or []:
        if (pr.get("id") or pr.get("providerId") or "") != "QNFO-OPS":
            continue
        for m in pr.get("models") or []:
            want = CANON_PARAM.get(m.get("id") or m.get("modelId"))
            if not want:
                continue
            m["contextWindow"] = want["contextWindow"]
            m["maxOutput"] = want["maxOutput"]

# ---------------- generic client (ChatBox / auto-discovered incl future SANNABOT) ----------------
def client_store(providers):
    """Return (provider_dict, drift_list) for the ops-endpoint provider inside a providers map."""
    for pid, pv in providers.items():
        host = str(pv.get("apiHost") or "")
        if OPS_HOST_MARK in host or OPS_HOST_MARK_NEW in host:
            drift = []
            for m in pv.get("models") or []:
                want = CANON_PARAM.get(m.get("modelId"))
                if not want:
                    continue
                for field, val in (("contextWindow", want["contextWindow"]), ("maxOutput", want["maxOutput"])):
                    if m.get(field) != val:
                        drift.append(pid + "/" + str(m.get("modelId")) + ":" + field + "=" + str(m.get(field)))
            return pv, drift
    return None, None

def client_fix(pv):
    for m in pv.get("models") or []:
        want = CANON_PARAM.get(m.get("modelId"))
        if not want:
            continue
        m["contextWindow"] = want["contextWindow"]
        m["maxOutput"] = want["maxOutput"]

def auto_candidate_paths():
    """ChatBox plus any top-level %APPDATA% app dir config/settings that looks client-like."""
    paths = [CHATBOX]
    try:
        for name in sorted(os.listdir(ROAM)):
            if not name or name.startswith(".") or name == "DeepChat":
                continue
            for fname in ("config.json", "settings.json"):
                p = os.path.join(ROAM, name, fname)
                if os.path.isfile(p) and os.path.getsize(p) < 5 * 1024 * 1024:
                    try:
                        txt = open(p, "r", encoding="utf-8", errors="ignore").read()
                        if OPS_HOST_MARK in txt or OPS_HOST_MARK_NEW in txt:
                            paths.append(p)
                    except Exception:
                        pass
    except Exception:
        pass
    seen = []
    for p in paths:
        if p not in seen:
            seen.append(p)
    return seen

# SESSION-PIN-SWEEP-1 (2026-09-18, canonical case: ops-exec toolCalls:0 recurrence):
# DeepChat freezes provider_id/model_id PER-SESSION in deepchat_sessions at session-creation
# time from whatever the 'deepchat' agent config was THEN. Fixing app_settings.defaultModel or
# agents.config_json only affects NEW sessions - it does NOT retroactively repair already-open
# sessions, which keep their frozen pin forever. This is the root mechanism behind repeated
# "ops-exec still fails" reports even after the global default was corrected: the user's actual
# open chat tabs never got the fix. NON_AGENTIC_MODELS = models proven (via AGENTIC-CANARY-1 on
# qnfo-chat-canary) to NOT emit client tool_calls under QNFO-OPS; any session pinned to one of
# these is silently broken for DeepChat's native agent loop and must be repaired. Only
# QNFO-OPS/{NON_AGENTIC_MODELS} rows are touched - deliberate user picks of other providers
# (anthropic/deepseek/etc.) are left alone; this fixes a proven-broken combination, not a
# preference.
NON_AGENTIC_MODELS = {"ops-exec", "ops-frontier", "ops-frontier-mini", "ops-frontier-reason"}

# SESSION-PIN-SWEEP-2 (2026-09-19, canonical case: 195/214 sessions pinned to the DIRECT
# deepseek provider -> DeepChat runs its own CLIENT tool loop -> local exec/run_code fail
# ("Session not running") -> run ends provider_error). ROOT-CAUSE-1: the 'deepchat' agent's
# config_json.model carried {"providerId":"deepseek"}, pinning EVERY new session to the direct
# DeepSeek API and bypassing the server-side executor (SERVER-SIDE-EXEC-100-1). SESSION-PIN-
# SWEEP-1 left these alone as "deliberate user picks" - wrong: they are the residue of the
# agent default, i.e. a proven-broken combination, not a preference. BROKEN_PROVIDERS is the
# allowlist of providers with no server-side executor path.
BROKEN_PROVIDERS = {"deepseek", "anthropic"}  # 2026-09-19 user directive: direct deepseek AND anthropic pins have NO server-side executor -> DeepChat runs its own CLIENT tool loop (SERVER-SIDE-EXEC-100-1 violation) -> rewrite to SESSION_KEY (ops-frontier) and KEEP them there (durability; supersedes the earlier "direct deepseek allowed as fallback" sentinel). Canonical case: ptR3pIaDrDOJDVcwSmDlb reverted to deepseek-v4-flash after a one-off manual UPDATE that had no re-probe.

# NON-TOOL-MODELS-1 (2026-09-19, user directive "apply C for true server-side tool execution"):
# ops-exec/ops-frontier/-mini/-reason run a PURE SERVER-SIDE agent loop and emit NO client
# tool_calls. DeepChat must treat them as non-tool (model_configs config.functionCall=False) so its
# client agent layer does NOT enable tool-mode and wait for tool_calls that never arrive (which
# surfaced as "Request failed"). With functionCall=False DeepChat sends a plain chat request, the
# worker runs its full server-side tool loop (gpt-5.5), and returns the final answer text.
NON_TOOL_MODELS = {"ops-exec", "ops-frontier", "ops-frontier-mini", "ops-frontier-reason"}

def dc_sessions_drift(c):
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(deepchat_sessions)")]
    except Exception:
        return []
    if "provider_id" not in cols or "model_id" not in cols:
        return []
    qmarks = ",".join("?" * len(NON_AGENTIC_MODELS))
    bp = ",".join("?" * len(BROKEN_PROVIDERS))
    rows = c.execute(
        "SELECT id, provider_id, model_id FROM deepchat_sessions "
        "WHERE (provider_id='QNFO-OPS' AND model_id IN (%s)) OR provider_id IN (%s)" % (qmarks, bp),
        tuple(NON_AGENTIC_MODELS) + tuple(BROKEN_PROVIDERS),
    ).fetchall()
    return [{"id": r[0], "provider_id": r[1], "model_id": r[2]} for r in rows]

def dc_sessions_fix(c):
    qmarks = ",".join("?" * len(NON_AGENTIC_MODELS))
    bp = ",".join("?" * len(BROKEN_PROVIDERS))
    c.execute(
        "UPDATE deepchat_sessions SET provider_id=?, model_id=? "
        "WHERE (provider_id='QNFO-OPS' AND model_id IN (%s)) OR provider_id IN (%s)" % (qmarks, bp),
        (SESSION_KEY["providerId"], SESSION_KEY["modelId"]) + tuple(NON_AGENTIC_MODELS) + tuple(BROKEN_PROVIDERS),
    )

# SESSION-PIN-CENSUS-1 (2026-09-19, canonical case: session ptR3pIaDrDOJDVcwSmDlb reverted to
# deepseek/deepseek-v4-flash after a one-off manual UPDATE; guard then reported
# deepchat_sessions.state="clean" because BROKEN_PROVIDERS is the no-op sentinel {"__disabled__"}).
# The sweep above deliberately repairs ONLY proven-broken combinations (direct-deepseek is an
# allowed gateway fallback per the 2026-09-19 directive), so a session on any other provider is
# left intact BY POLICY. That is fine - but the guard must NOT then report an unqualified "clean".
# This read-only census makes the residual pins VISIBLE in every run so "clean" can never hide
# them (DETECTION-NOT-REMEDIATION-1 / FILING-NOT-FIXING-1: a detector that hides what it chose not
# to repair is a false negative). It repairs nothing and never changes rc.
def dc_sessions_census(c):
    try:
        rows = c.execute(
            "SELECT provider_id, model_id, COUNT(*) FROM deepchat_sessions GROUP BY 1,2"
        ).fetchall()
    except Exception:
        return {}
    by_pin = {"%s/%s" % (p, m): n for p, m, n in rows}
    desired = "%s/%s" % (SESSION_KEY["providerId"], SESSION_KEY["modelId"])
    # Residual = sessions NOT on the desired key AND NOT on the QNFO-OPS server-side-executor
    # provider. These run DeepChat's CLIENT tool loop instead of the server-side executor
    # (SERVER-SIDE-EXEC-100-1). Direct deepseek is an allowed fallback, so they are surfaced,
    # never silently rewritten.
    residual = {
        k: v for k, v in by_pin.items()
        if k != desired and not k.startswith("QNFO-OPS/")
    }
    return {
        "total": sum(by_pin.values()),
        "by_pin": by_pin,
        "not_desired_key": {k: v for k, v in by_pin.items() if k != desired},
        "residual_off_server_side": residual,
    }

# AGENT-MODEL-SWEEP-1 (2026-09-19): the 6th/7th model-key locations. agents.config_json holds
# model / assistantModel / defaultModelPreset, which DeepChat copies into deepchat_sessions AT
# SESSION CREATION. Sweeping app_settings.defaultModel alone is necessary but NOT sufficient: a
# deepseek ref here re-pins every new session and silently re-creates SESSION-PIN-SWEEP-2.
AGENT_MODEL_KEYS = ("model", "assistantModel", "defaultModelPreset")

def dc_agents_drift(c):
    bad = []
    try:
        rows = c.execute("SELECT id, config_json FROM agents").fetchall()
    except Exception:
        return []
    for aid, cfg in rows:
        if not cfg:
            continue
        try:
            o = json.loads(cfg)
        except Exception:
            continue
        for k in AGENT_MODEL_KEYS:
            v = o.get(k)
            if isinstance(v, dict) and v.get("providerId") in BROKEN_PROVIDERS:
                bad.append({"agent": aid, "key": k, "value": v})
    return bad

def dc_agents_fix(c):
    for aid, cfg in c.execute("SELECT id, config_json FROM agents").fetchall():
        if not cfg:
            continue
        try:
            o = json.loads(cfg)
        except Exception:
            continue
        changed = False
        for k in AGENT_MODEL_KEYS:
            v = o.get(k)
            if isinstance(v, dict) and v.get("providerId") in BROKEN_PROVIDERS:
                o[k] = {"providerId": "QNFO-OPS", "modelId": "ops"}
                changed = True
        if changed:
            c.execute("UPDATE agents SET config_json=?, updated_at=? WHERE id=?",
                      (json.dumps(o, ensure_ascii=False), now(), aid))


# PROVIDER-MODELS-SWEEP-1 (2026-09-18): DeepChat's model PICKER reads provider_models
# (source='provider', re-synced from the worker's /v1/models endpoint), NOT model_configs.
# A model present in model_configs but absent from provider_models is INVISIBLE in the picker
# ("there is no ops-frontier in DeepChat" canonical case). The worker must advertise these in
# /v1/models, but this guard belt-and-suspenders them into provider_models every run so a
# /v1/models regression cannot silently drop them again.
FRONTIER_MODEL_IDS = ["ops-frontier", "ops-frontier-mini", "ops-frontier-reason"]

def dc_provider_models_drift(c):
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(provider_models)")]
    except Exception:
        return []
    if "model_id" not in cols:
        return []
    present = set(r[0] for r in c.execute("SELECT model_id FROM provider_models WHERE provider_id='QNFO-OPS'").fetchall())
    return [m for m in FRONTIER_MODEL_IDS if m not in present]

def dc_provider_models_fix(c):
    import json as _json
    nowms = int(time.time() * 1000)
    for i, mid in enumerate(FRONTIER_MODEL_IDS):
        mj = _json.dumps({"id": mid, "name": mid, "group": "frontier", "providerId": "QNFO-OPS", "isCustom": False, "ownedBy": "qnfo"})
        c.execute("INSERT OR REPLACE INTO provider_models (provider_id, model_id, source, name, group_name, sort_order, model_json, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                  ("QNFO-OPS", mid, "provider", mid, "frontier", 10 + i, mj, nowms, nowms))

def main():
    out = {"ts": now(), "desired_key": DESIRED_KEY, "canon_params": CANON_PARAM, "stores": {}}
    rc = 0
    # DeepChat DB
    if os.path.exists(DB):
        c = sqlite3.connect(DB, timeout=10)
        try:
            b = dc_db_drift(c)
            out["stores"]["deepchat_db"] = {"drift_before": b}
            if b:
                dc_db_fix(c); c.commit()
                out["stores"]["deepchat_db"]["fixed"] = True
            rb = dc_db_drift(c)
            out["stores"]["deepchat_db"]["readback"] = rb
            if rb:
                out["stores"]["deepchat_db"]["state"] = "verify-failed"; rc = 2
            else:
                out["stores"]["deepchat_db"]["state"] = "fixed" if b else "clean"
        except Exception as e:
            out["stores"]["deepchat_db"] = {"state": "error", "error": str(e)}; rc = 1
        finally:
            c.close()
    # NON-TOOL-MODELS-1: functionCall=False pin for server-side-loop models.
    if os.path.exists(DB):
        c = sqlite3.connect(DB, timeout=10)
        try:
            fb = dc_functioncall_drift(c)
            out["stores"]["deepchat_functioncall"] = {"drift_before": fb}
            if fb:
                dc_functioncall_fix(c); c.commit()
                out["stores"]["deepchat_functioncall"]["fixed"] = True
            frb = dc_functioncall_drift(c)
            out["stores"]["deepchat_functioncall"]["readback"] = frb
            if frb:
                out["stores"]["deepchat_functioncall"]["state"] = "verify-failed"; rc = 2
            else:
                out["stores"]["deepchat_functioncall"]["state"] = "fixed" if fb else "clean"
        except Exception as e:
            out["stores"]["deepchat_functioncall"] = {"state": "error", "error": str(e)}; rc = 1
        finally:
            c.close()
    # SESSION-PIN-SWEEP-1: per-session frozen model pins (deepchat_sessions), separate
    # connection/commit from the app_settings pass above so a failure here never blocks it.
    if os.path.exists(DB):
        c = sqlite3.connect(DB, timeout=10)
        try:
            sb = dc_sessions_drift(c)
            out["stores"]["deepchat_sessions"] = {"drift_before": sb}
            if sb:
                dc_sessions_fix(c); c.commit()
                out["stores"]["deepchat_sessions"]["fixed"] = True
            srb = dc_sessions_drift(c)
            out["stores"]["deepchat_sessions"]["readback"] = srb
            if srb:
                out["stores"]["deepchat_sessions"]["state"] = "verify-failed"; rc = 2
            else:
                out["stores"]["deepchat_sessions"]["state"] = "fixed" if sb else "clean"
            # SESSION-PIN-CENSUS-1: read-only visibility of residual (by-policy) pins.
            out["stores"]["deepchat_sessions"]["census"] = dc_sessions_census(c)
        except Exception as e:
            out["stores"]["deepchat_sessions"] = {"state": "error", "error": str(e)}; rc = 1
        finally:
            c.close()
    # AGENT-MODEL-SWEEP-1: agents.config_json model keys (the source of new-session pins).
    if os.path.exists(DB):
        c = sqlite3.connect(DB, timeout=10)
        try:
            ab = dc_agents_drift(c)
            out["stores"]["deepchat_agents"] = {"drift_before": ab}
            if ab:
                dc_agents_fix(c); c.commit()
                out["stores"]["deepchat_agents"]["fixed"] = True
            arb = dc_agents_drift(c)
            out["stores"]["deepchat_agents"]["readback"] = arb
            if arb:
                out["stores"]["deepchat_agents"]["state"] = "verify-failed"; rc = 2
            else:
                out["stores"]["deepchat_agents"]["state"] = "fixed" if ab else "clean"
        except Exception as e:
            out["stores"]["deepchat_agents"] = {"state": "error", "error": str(e)}; rc = 1
        finally:
            c.close()
        # PROVIDER-MODELS-SWEEP-1: ensure frontier models remain in provider_models (the picker).
    if os.path.exists(DB):
        c = sqlite3.connect(DB, timeout=10)
        try:
            pb = dc_provider_models_drift(c)
            out["stores"]["deepchat_provider_models"] = {"drift_before": pb}
            if pb:
                dc_provider_models_fix(c); c.commit()
                out["stores"]["deepchat_provider_models"]["fixed"] = True
            prb = dc_provider_models_drift(c)
            out["stores"]["deepchat_provider_models"]["readback"] = prb
            if prb:
                out["stores"]["deepchat_provider_models"]["state"] = "verify-failed"; rc = 2
            else:
                out["stores"]["deepchat_provider_models"]["state"] = "fixed" if pb else "clean"
        except Exception as e:
            out["stores"]["deepchat_provider_models"] = {"state": "error", "error": str(e)}; rc = 1
        finally:
            c.close()
# DeepChat JSON
    if os.path.exists(JS):
        try:
            d = jload(JS)
            b = dc_js_drift(d)
            out["stores"]["deepchat_json"] = {"drift_before": b}
            if b:
                dc_js_fix(d)
                atomic_json(JS, d)
                out["stores"]["deepchat_json"]["fixed"] = True
            rb = dc_js_drift(jload(JS))
            out["stores"]["deepchat_json"]["readback"] = rb
            out["stores"]["deepchat_json"]["state"] = "verify-failed" if rb else ("fixed" if b else "clean")
            if rb: rc = 2
        except Exception as e:
            out["stores"]["deepchat_json"] = {"state": "error", "error": str(e)}; rc = 1
    # NON-TOOL-MODELS-1: app-settings.json capability mirror (drop tool_use).
    if os.path.exists(JS):
        try:
            d = jload(JS)
            fb = dc_js_functioncall_drift(d)
            out["stores"]["deepchat_json_functioncall"] = {"drift_before": fb}
            if fb:
                dc_js_functioncall_fix(d)
                atomic_json(JS, d)
                out["stores"]["deepchat_json_functioncall"]["fixed"] = True
            frb = dc_js_functioncall_drift(jload(JS))
            out["stores"]["deepchat_json_functioncall"]["readback"] = frb
            out["stores"]["deepchat_json_functioncall"]["state"] = "verify-failed" if frb else ("fixed" if fb else "clean")
            if frb: rc = 2
        except Exception as e:
            out["stores"]["deepchat_json_functioncall"] = {"state": "error", "error": str(e)}; rc = 1
    # generic client stores (ChatBox + auto-discovered, incl future SANNABOT)
    discovered = []
    for p in auto_candidate_paths():
        try:
            d = jload(p)
        except Exception as e:
            out["stores"][p] = {"state": "unparseable", "error": str(e)}
            continue
        providers = None
        if isinstance(d, dict):
            if isinstance(d.get("providers"), dict):
                providers = d["providers"]
            elif isinstance(d.get("settings"), dict) and isinstance(d["settings"].get("providers"), dict):
                providers = d["settings"]["providers"]
        if not providers:
            continue
        pv, drift = client_store(providers)
        if pv is None:
            continue
        discovered.append(p)
        rec = {"drift_before": drift}
        if drift:
            client_fix(pv)
            atomic_json(p, d)
            rec["fixed"] = True
        # read-back
        try:
            d2 = jload(p)
            providers2 = None
            if isinstance(d2, dict):
                if isinstance(d2.get("providers"), dict):
                    providers2 = d2["providers"]
                elif isinstance(d2.get("settings"), dict) and isinstance(d2["settings"].get("providers"), dict):
                    providers2 = d2["settings"]["providers"]
            _, rb = client_store(providers2 or {})
            rec["readback"] = rb
            rec["state"] = "verify-failed" if rb else ("fixed" if drift else "clean")
            if rb: rc = 2
        except Exception as e:
            rec["readback_error"] = str(e); rc = 1
        out["stores"][p] = rec
    out["ops_client_stores"] = discovered
    out["state"] = "clean" if rc == 0 else ("error" if rc == 1 else "verify-failed")
    print(json.dumps(out))
    return rc

if __name__ == "__main__":
    sys.exit(main())
