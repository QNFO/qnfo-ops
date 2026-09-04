#!/usr/bin/env python3
"""model-guard.py - permanent DEEPCHAT-DEFAULT-MODEL-1 drift guard (2026-09-02).
Canonical: QNFO/qnfo-ops/scripts/model_guard.py (mirror .deepchat/scripts).
OPS-EXEC-DEFAULT-1 (2026-09-04): canonical default is QNFO-OPS/ops-exec (hybrid server/client tool loop); the deepseek-v4-flash relay stays available as an explicit model.
Recurrence-ZERO-1 guard for MODEL-KEY-FILE-DRIFT-1 (app save re-drifts preferredModel to
deepseek-v4-pro while the DB stays flash). Aligns BOTH stores (MODEL-KEY-DB-ROOT-SOURCE-1:
DB rows first, then JSON, then read-back both). Idempotent; silent when clean.
Trigger (2026-09-03): Windows Task Scheduler 'QNFO-ModelKey-Guard' runs this script every 30 min (schtasks MINUTE /mo 30; tightened from daily 07:00 after JSON preferredModel re-drifted to deepseek-v4-pro <3h after the daily fix - MODEL-KEY-GUARD-HOURLY-1). Device-bound local-config write: CLOUD-FRONTEND-ONLY-1 compliant; the DeepChat local cron 5-row registry is unchanged.
Exit codes: 0=clean/fixed 1=check-error 2=failed-to-fix.
"""
import json, os, sqlite3, sys, tempfile, datetime

DESIRED = {"providerId": "QNFO-OPS", "modelId": "ops-exec"}  # OPS-EXEC-DEFAULT-1 (2026-09-04): main-agent default = hybrid ops-exec loop (deepseek-v4-flash relay remains for explicit relay selection)
APP_DIR = os.path.expandvars(r"%APPDATA%\DeepChat")
DB = os.path.join(APP_DIR, "app_db", "agent.db")
JS = os.path.join(APP_DIR, "app-settings.json")

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def db_drift(c):
    drift = []
    for k in ("defaultModel", "preferredModel"):
        row = c.execute("SELECT value_json FROM app_settings WHERE key=?", (k,)).fetchone()
        if row is None:
            drift.append(k + ":missing")
            continue
        try:
            v = json.loads(row[0])
        except Exception:
            drift.append(k + ":unparseable")
            continue
        if v != DESIRED:
            drift.append(k + ":" + json.dumps(v))
    return drift

def fix_db(c):
    for k in ("defaultModel", "preferredModel"):
        c.execute("UPDATE app_settings SET value_json=?, updated_at=? WHERE key=?",
                  (json.dumps(DESIRED), now(), k))

def js_drift(d):
    drift = []
    for k in ("defaultModel", "preferredModel"):
        v = d.get(k)
        if v != DESIRED:
            drift.append(k + ":" + json.dumps(v))
    return drift

def main():
    out = {"ts": now(), "desired": DESIRED}
    if not os.path.exists(JS):
        out["state"] = "json-missing"
        print(json.dumps(out)); return 1
    try:
        d = json.load(open(JS, encoding="utf-8"))
    except Exception as e:
        out["state"] = "json-unparseable"; out["error"] = str(e)
        print(json.dumps(out)); return 1
    jdrift = js_drift(d)
    c = sqlite3.connect(DB, timeout=10)
    try:
        bdrift = db_drift(c)
    except Exception as e:
        c.close()
        out["state"] = "db-error"; out["error"] = str(e)
        print(json.dumps(out)); return 1
    out["db_drift_before"] = bdrift
    out["js_drift_before"] = jdrift
    if not bdrift and not jdrift:
        c.close()
        out["state"] = "clean"
        print(json.dumps(out)); return 0
    # fix DB rows
    try:
        fix_db(c); c.commit()
    except Exception as e:
        c.close()
        out["state"] = "db-fix-failed"; out["error"] = str(e)
        print(json.dumps(out)); return 2
    # fix JSON atomically
    try:
        for k in ("defaultModel", "preferredModel"):
            d[k] = DESIRED
        fd, tmp = tempfile.mkstemp(dir=APP_DIR, prefix="app-settings.", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, JS)
    except Exception as e:
        c.close()
        out["state"] = "js-fix-failed"; out["error"] = str(e)
        print(json.dumps(out)); return 2
    # read-back verify both
    try:
        d2 = json.load(open(JS, encoding="utf-8"))
        rb_js = js_drift(d2)
        rb_db = db_drift(c)
        c.close()
        out["readback_js"] = rb_js
        out["readback_db"] = rb_db
        if not rb_js and not rb_db:
            out["state"] = "fixed"
            print(json.dumps(out)); return 0
        out["state"] = "fix-verify-failed"
        print(json.dumps(out)); return 2
    except Exception as e:
        c.close()
        out["state"] = "readback-error"; out["error"] = str(e)
        print(json.dumps(out)); return 1

if __name__ == "__main__":
    sys.exit(main())
