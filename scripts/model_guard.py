#!/usr/bin/env python3
"""model_guard.py v3 - OPS-SETTINGS-IMMUTABLE-1 permanent drift guard (2026-09-09).
HARDEN-AND-MANDATE (user directive 2026-09-09, applied systemwide): the canonical ops-exec
settings below are IMMUTABLE - no agent, session, or process may change them:
  model key        : QNFO-OPS / ops-exec in ALL four DeepChat keys (DB + JSON)
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

DESIRED_KEY = {"providerId": "QNFO-OPS", "modelId": "ops-exec"}
# parameter canon: DeepChat config_json keys (model_configs) + JSON contextWindow/maxOutput
CANON_PARAM = {
    "ops-exec": {"maxTokens": 393216, "contextLength": 1048576, "timeout": 3600000,
                 "contextWindow": 1048576, "maxOutput": 393216},
    "deepseek-v4-flash": {"maxTokens": 393216, "contextLength": 1048576, "timeout": 3600000,
                          "contextWindow": 1048576, "maxOutput": 393216},
}
OPS_HOST_MARK = "qnfo-ops.q08.workers.dev"

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
        if OPS_HOST_MARK in host:
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
                        if OPS_HOST_MARK in txt:
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
