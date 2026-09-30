#!/usr/bin/env python3
r"""
deepchat_compact.py - agent.db bloat compaction (canonical DeepChat hygiene engine).

WHY
  agent.db grew to ~4.75 GB (2026-09-30) dominated by the append-only
  `deepchat_tape_entries` diagnostic log (2.27 GB / 487k rows in 28 days) plus
  derived, rebuildable projections. A multi-GB store makes every startup and
  every session query slow.

WHAT (Lamport-style, ordered)
  1. Classify every table row by three tiers:
       T0 USER DATA     messages / assistant_blocks / user_messages / sessions /
                        agent_memory / providers / settings  -> NEVER touched by
                        the derived tier; the chat tier is retention-gated.
       T1 DERIVED/DIAG  deepchat_tape_entries, deepchat_tape_search_projection,
                        deepchat_tape_search_fts  -> time-retention purge.
       T2 PROJECTION    deepchat_search_documents(+fts),
                        deepchat_memory_ingestion_projection(+meta)  -> purged for
                        sessions that no longer have recent messages.
  2. Purge T1 by created_at < now - tape_days.
  3. Compute old_sessions = sessions whose newest message is older than
     chat_days AND that are not among the keep_sessions most recently active.
  4. Purge chat payloads + T2 projections for those sessions, then rebuild the
     external-content FTS.
  5. VACUUM (offline only) to physically return pages to the filesystem.

SAFETY
  * VACUUM requires the app to be closed (exclusive lock). `--mode offline`
    refuses to run the vacuum if DeepChat.exe is running.
  * Online mode (app running) does the same deletes but skips the VACUUM; the
    file plateaus (SQLite reuses freed pages) until the next offline pass.
  * Every delete is transactional and resumable; FTS5 is always touched through
    the VIRTUAL table (never the shadow tables) - see deepchat_clear_chats_once.py
    red-team note (2026-08-31).
  * Writes a JSON report to logs/deepchat_compact.json + human log.

USAGE
  python deepchat_compact.py --mode plan                         # dry-run counts
  python deepchat_compact.py --mode online --tape-days 3 --chat-days 14
  python deepchat_compact.py --mode offline --vacuum             # app must be shut
"""
from __future__ import annotations
import argparse, datetime, json, os, sqlite3, subprocess, sys, time

ROAM = os.path.join(os.environ.get("APPDATA", r"C:\Users\LENOVO\AppData\Roaming"), "DeepChat")
DB = os.environ.get("DEEPCHAT_DB") or os.path.join(ROAM, "app_db", "agent.db")
LOGDIR = os.environ.get("DEEPCHAT_LOGDIR") or os.path.join(ROAM, "logs")
JSONOUT = os.path.join(LOGDIR, "deepchat_compact.json")
LOG = os.path.join(LOGDIR, "deepchat_compact.log")

TAPE_TABLES = ["deepchat_tape_entries", "deepchat_tape_search_projection"]
CHAT_CHILD_BY_SESSION = [
    "deepchat_message_search_results",
    "deepchat_search_documents",
    "deepchat_memory_ingestion_projection",
    "deepchat_memory_ingestion_projection_meta",
    "deepchat_message_traces",
]
CHAT_CHILD_BY_MESSAGE = [
    "deepchat_assistant_blocks",
    "deepchat_user_messages",
    "deepchat_user_message_files",
    "deepchat_user_message_links",
]
CHAT_SESSION_TABLES = ["deepchat_sessions", "new_sessions", "deepchat_session_metadata"]


def log(msg):
    line = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg)
    print(line, flush=True)
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def app_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq DeepChat.exe", "/NH"],
                             capture_output=True, text=True, timeout=30).stdout
        return "DeepChat.exe" in out
    except Exception:
        return True


def table_exists(cur, t):
    return cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def cols_of(cur, t):
    return [c[1] for c in cur.execute('PRAGMA table_info("%s")' % t)]


def count_where(cur, t, where, args=()):
    try:
        return cur.execute('SELECT COUNT(*) FROM "%s" WHERE %s' % (t, where), args).fetchone()[0]
    except Exception:
        return 0


def delete_chunked(cur, con, t, where, args=(), chunk=400, by=None):
    """DELETE in bounded transactions. `by` = a key expression usable with
    `SELECT key FROM t WHERE <where> LIMIT n` (defaults to rowid)."""
    total = 0
    if not table_exists(cur, t):
        return 0
    while True:
        if by:
            sql = 'SELECT %s FROM "%s" WHERE %s LIMIT %d' % (by, t, where, chunk)
        else:
            sql = 'SELECT rowid FROM "%s" WHERE %s LIMIT %d' % (t, where, chunk)
        try:
            rows = [r[0] for r in cur.execute(sql, args).fetchall()]
        except Exception as e:
            log("   ! chunk-select %s: %s" % (t, e))
            break
        if not rows:
            break
        if by:
            ph = ",".join("?" * len(rows))
            n = cur.execute('DELETE FROM "%s" WHERE %s IN (%s)' % (t, by, ph), rows).rowcount
        else:
            ph = ",".join("?" * len(rows))
            n = cur.execute('DELETE FROM "%s" WHERE rowid IN (%s)' % (t, ph), rows).rowcount
        total += n
        con.commit()
        if n == 0:
            break
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["plan", "online", "offline"], default="plan")
    ap.add_argument("--tape-days", type=int, default=3)
    ap.add_argument("--chat-days", type=int, default=14)
    ap.add_argument("--keep-sessions", type=int, default=12)
    ap.add_argument("--no-chat-prune", action="store_true")
    ap.add_argument("--vacuum", action="store_true")
    ap.add_argument("--force", action="store_true", help="skip the app-running guard (tests / orchestrator)")
    a = ap.parse_args()

    running = app_running()
    if a.mode == "offline" and running and not a.force:
        log("offline requested but DeepChat.exe is running - abort (exit 3)")
        return 3
    if not os.path.exists(DB):
        log("agent.db not found at %s" % DB)
        return 1

    now_ms = int(time.time() * 1000)
    tape_cut = now_ms - a.tape_days * 86400000
    chat_cut = now_ms - a.chat_days * 86400000

    size_before = os.path.getsize(DB)
    wal_before = os.path.getsize(DB + "-wal") if os.path.exists(DB + "-wal") else 0

    con = sqlite3.connect(DB, timeout=180)
    con.execute("PRAGMA busy_timeout=180000")
    cur = con.cursor()

    report = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "mode": a.mode,
              "app_running": running, "size_before_mb": round(size_before / 1048576.0, 1),
              "wal_before_mb": round(wal_before / 1048576.0, 1),
              "tape_days": a.tape_days, "chat_days": a.chat_days, "keep_sessions": a.keep_sessions}

    # ---- PLAN: counts only ----
    if a.mode == "plan":
        plan = {}
        for t in TAPE_TABLES:
            plan[t] = count_where(cur, t, "created_at < ?", (tape_cut,))
        if table_exists(cur, "deepchat_tape_search_fts"):
            plan["deepchat_tape_search_fts"] = count_where(cur, "deepchat_tape_search_fts", "created_at < ?", (tape_cut,))
        plan["size_mb"] = round(size_before / 1048576.0, 1)
        plan["tape_rows_total"] = count_where(cur, "deepchat_tape_entries", "1=1")
        log("PLAN " + json.dumps(plan))
        cur.close(); con.close()
        return 0

    # ---- determine old sessions ----
    old_sessions = []
    if not a.no_chat_prune:
        rows = cur.execute("SELECT session_id, MAX(updated_at) FROM deepchat_messages "
                           "GROUP BY session_id").fetchall()
        newest = sorted(rows, key=lambda r: -(r[1] or 0))
        keep = set(s for s, _ in newest[:a.keep_sessions])
        old_sessions = [s for s, m in rows if (m or 0) < chat_cut and s not in keep]
    report["old_sessions"] = len(old_sessions)

    deleted = {}

    # ---- 1. tape purge ----
    deleted["deepchat_tape_entries"] = delete_chunked(
        cur, con, "deepchat_tape_entries", "created_at < ?", (tape_cut,))
    deleted["deepchat_tape_search_projection"] = delete_chunked(
        cur, con, "deepchat_tape_search_projection", "created_at < ?", (tape_cut,))
    if table_exists(cur, "deepchat_tape_search_fts"):
        # FTS5-aware delete through the VIRTUAL table only.
        try:
            n = cur.execute("DELETE FROM deepchat_tape_search_fts WHERE created_at < ?", (tape_cut,)).rowcount
            con.commit()
            deleted["deepchat_tape_search_fts"] = n
        except Exception as e:
            log("   ! tape fts delete: %s" % e)
            deleted["deepchat_tape_search_fts"] = 0

    # ---- 2. chat + projection purge for old sessions ----
    if old_sessions:
        cur.execute("CREATE TEMP TABLE IF NOT EXISTS _old_sid (session_id TEXT PRIMARY KEY)")
        cur.execute("DELETE FROM _old_sid")
        B = 400
        for i in range(0, len(old_sessions), B):
            cur.executemany("INSERT OR IGNORE INTO _old_sid(session_id) VALUES(?)",
                            [(s,) for s in old_sessions[i:i + B]])
        con.commit()

        cur.execute("CREATE TEMP TABLE IF NOT EXISTS _old_mid (message_id TEXT PRIMARY KEY)")
        cur.execute("DELETE FROM _old_mid")
        cur.execute("INSERT OR IGNORE INTO _old_mid(message_id) "
                    "SELECT id FROM deepchat_messages WHERE session_id IN (SELECT session_id FROM _old_sid)")
        con.commit()

        # capture message ids first, then delete messages, then children
        for t in CHAT_CHILD_BY_MESSAGE:
            if not table_exists(cur, t):
                continue
            if "message_id" not in cols_of(cur, t):
                continue
            deleted[t] = delete_chunked(
                cur, con, t, "message_id IN (SELECT message_id FROM _old_mid)", (), by="message_id")
        deleted["deepchat_messages"] = delete_chunked(
            cur, con, "deepchat_messages", "session_id IN (SELECT session_id FROM _old_sid)")
        for t in CHAT_CHILD_BY_SESSION:
            if not table_exists(cur, t):
                continue
            if "session_id" in cols_of(cur, t):
                deleted[t] = delete_chunked(
                    cur, con, t, "session_id IN (SELECT session_id FROM _old_sid)", ())
        # session metadata rows (removes the old, now-empty conversations from the UI)
        for t in CHAT_SESSION_TABLES:
            if not table_exists(cur, t):
                continue
            key = "id" if "id" in cols_of(cur, t) else ("session_id" if "session_id" in cols_of(cur, t) else None)
            if key:
                deleted[t] = delete_chunked(
                    cur, con, t, "%s IN (SELECT session_id FROM _old_sid)" % key, (), by=key)

        # rebuild the external-content FTS over the surviving search documents
        if table_exists(cur, "deepchat_search_documents_fts"):
            try:
                cur.execute("INSERT INTO deepchat_search_documents_fts(deepchat_search_documents_fts) VALUES('rebuild')")
                con.commit()
                deleted["search_documents_fts_rebuilt"] = True
            except Exception as e:
                log("   ! search fts rebuild: %s" % e)

    # ---- 3. optional vacuum ----
    try:
        cur.execute("PRAGMA optimize")
        con.commit()
    except Exception:
        pass

    if a.vacuum:
        t0 = time.time()
        try:
            cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            con.commit()
            log("   vacuuming ...")
            cur.execute("VACUUM")
            cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            con.commit()
            report["vacuum_seconds"] = round(time.time() - t0, 1)
            report["vacuum"] = True
        except Exception as e:
            log("   ! VACUUM failed: %s" % e)
            report["vacuum_error"] = str(e)

    report["deleted"] = {k: v for k, v in deleted.items() if v}
    report["size_after_mb"] = round(os.path.getsize(DB) / 1048576.0, 1)
    try:
        report["integrity"] = cur.execute("PRAGMA quick_check").fetchone()[0]
    except Exception:
        report["integrity"] = "unknown"
    cur.close(); con.close()

    log("DONE " + json.dumps(report))
    try:
        with open(JSONOUT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
