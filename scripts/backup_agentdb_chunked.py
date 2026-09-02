#!/usr/bin/env python3
"""backup_agentdb_chunked.py - agent.db backup (permanent, 2026-09-02).
v1.2 (2026-09-02, user directive + follow-up): SETTINGS/MEMORY SPLIT. User rejected
whole-DB backup (agent.db ~1.2 GB) as unsustainable; chat threads are expendable but
the settings/config state is important. v1.1 pruned chat content (1223 MB -> 116 MB).
v1.2 additionally splits DURABLE MEMORY into its own R2 artifact (option: "Split memory
separately"): the main agent.db backup now ALSO removes agent_memory* content so it stays
minimal, and a separate agent-memory.db object (memory tables + FTS intact) is uploaded
under the same stamp. Restore: settings from agent.db; memory independently from
agent-memory.db (attach + copy agent_memory* tables if desired). LIVE DB never modified.
Canonical: QNFO/qnfo-ops/scripts/backup_agentdb_chunked.py (mirror .deepchat/scripts).
"""
import os, sys, json, time, hashlib, sqlite3, urllib.request, urllib.error

TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', '')
ACCT = 'edb167b78c9fb901ea5bca3ce58ccc4b'
BUCKET = 'qnfo-backups'
ROAM = r'C:/Users/LENOVO/AppData/Roaming/DeepChat'
CHUNK = 90 * 1024 * 1024  # 90 MiB < REST ~100 MB cap
PREFIX = 'deepchat/' + time.strftime('%Y/%m') + '/'
STAMP = time.strftime('%Y%m%d-%H%M%S')
MEMORY_BACKUP = os.environ.get('MEMORY_BACKUP', '1') == '1'

# Chat-thread CONTENT tables (expendable; per-thread SETTINGS live in deepchat_sessions/new_sessions which are KEPT)
PRUNE_TABLES = [
    'acp_sessions', 'acp_turns',
    'deepchat_assistant_blocks', 'deepchat_memory_ingestion_projection',
    'deepchat_memory_ingestion_projection_meta', 'deepchat_message_search_results',
    'deepchat_messages', 'deepchat_pending_inputs', 'deepchat_search_documents',
    'deepchat_tape_entries', 'deepchat_tape_search_projection', 'deepchat_tape_search_projection_meta',
    'deepchat_user_message_files', 'deepchat_user_message_links', 'deepchat_user_messages',
    'live_delegation_events', 'live_delegation_turns', 'live_delegations',
]
# Durable memory tables - REMOVED from the main (settings) backup, exported separately
MEMORY_TABLES = ['agent_memory', 'agent_memory_tombstone', 'agent_memory_clear_job',
                 'agent_memory_derivation', 'agent_memory_dirty', 'agent_memory_fts_meta',
                 'agent_memory_fts', 'agent_memory_fts_data', 'agent_memory_fts_idx',
                 'agent_memory_fts_docsize', 'agent_memory_fts_config',
                 'agent_memory_audit', 'agent_memory_directive']
FTS_DELETE_ALL = ['deepchat_search_documents_fts', 'agent_memory_fts']   # external-content FTS5 -> delete-all
FTS_PLAIN_DELETE = ['deepchat_tape_search_fts']      # regular-content FTS5 -> DELETE FROM works

def upload(key, data):
    url = f'https://api.cloudflare.com/client/v4/accounts/{ACCT}/r2/buckets/{BUCKET}/objects/{key}'
    req = urllib.request.Request(url, method='PUT', data=data, headers={
        'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/octet-stream',
        'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode('utf-8')).get('success', False)

def clear_table_rows(db_path, tables, commit_each=False):
    """DELETE all rows from the given tables (content tables only - never FTS shadow)."""
    con = sqlite3.connect(db_path, timeout=60)
    con.execute('PRAGMA busy_timeout=15000')
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r[0] for r in cur.fetchall()}
    removed = 0
    for t in tables:
        if t in names:
            try:
                cur.execute('DELETE FROM "' + t + '"')
                removed += cur.rowcount
                if commit_each:
                    con.commit()
            except Exception as e:
                print('  [WARN] del', t, str(e)[:100], flush=True)
    # FTS: external-content -> delete-all special command; regular FTS -> DELETE FROM
    for t in FTS_DELETE_ALL:
        if t in names:
            try:
                cur.execute('INSERT INTO "' + t + '"("' + t + '") VALUES("delete-all")')
            except Exception as e:
                print('  [WARN] fts delete-all', t, str(e)[:100], flush=True)
    for t in FTS_PLAIN_DELETE:
        if t in names:
            try:
                cur.execute('DELETE FROM "' + t + '"')
            except Exception as e:
                print('  [WARN] fts delete', t, str(e)[:100], flush=True)
    con.commit()
    try:
        cur.execute('VACUUM')
        con.commit()
    except Exception as e:
        print('  [WARN] vacuum', str(e)[:100], flush=True)
    con.close()
    return removed

def snapshot(db_src, suffix):
    tmp = os.path.join(os.environ.get('TEMP', 'C:/Users/LENOVO/AppData/Local/Temp'),
                       'agent-snapshot-' + STAMP + '-' + suffix + '.db')
    try:
        os.remove(tmp)
    except Exception:
        pass
    src = sqlite3.connect(db_src, timeout=60)
    dst = sqlite3.connect(tmp)
    src.backup(dst)
    dst.close(); src.close()
    return tmp

def upload_object(path, key):
    size = os.path.getsize(path)
    if size <= 95 * 1024 * 1024:
        with open(path, 'rb') as f:
            data = f.read()
        ok = upload(key, data)
        return size, 1, ok
    parts = (size + CHUNK - 1) // CHUNK
    keybase = key + '/'
    sha = hashlib.sha256()
    n = 0
    with open(path, 'rb') as f:
        while True:
            data = f.read(CHUNK)
            if not data:
                break
            n += 1
            sha.update(data)
            ok = upload(keybase + 'part_%03d_of_%03d' % (n, parts), data)
            if not ok:
                print('ERROR uploading part %d' % n, flush=True)
                return size, n, False
    manifest = {
        'object': os.path.basename(key), 'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'bytes': size, 'parts': parts, 'chunk_bytes': CHUNK, 'sha256': sha.hexdigest(),
        'restore': 'cat part_*_of_%03d > %s' % (parts, os.path.basename(key))}
    ok = upload(keybase + 'manifest.json', json.dumps(manifest).encode('utf-8'))
    return size, n, ok and True

def main():
    if not TOKEN:
        print('ERROR: CLOUDFLARE_API_TOKEN missing'); return 1
    db_src = os.path.join(ROAM, 'app_db', 'agent.db')
    try:
        # ---- MAIN SETTINGS BACKUP (chats + memory pruned) ----
        t1 = snapshot(db_src, 'settings')
        before = os.path.getsize(t1)
        removed = clear_table_rows(t1, PRUNE_TABLES + MEMORY_TABLES)
        size = os.path.getsize(t1)
        print('prune settings: removed %d rows, %d -> %d bytes (%.1f%% saved)' % (
            removed, before, size, (100.0 * (before - size) / before) if before else 0), flush=True)
        sbytes, sparts, sok = upload_object(t1, PREFIX + STAMP + '/agent.db')
        print('agent.db settings backup: ' + ('OK' if sok else 'FAIL') + ' (%d parts, %d bytes)' % (sparts, sbytes), flush=True)
        try: os.remove(t1)
        except Exception: pass
        # ---- MEMORY BACKUP (separate artifact; agent_memory* only) ----
        if MEMORY_BACKUP:
            t2 = snapshot(db_src, 'memory')
            con = sqlite3.connect(t2, timeout=60); cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            drop = []
            for (name,) in cur.fetchall():
                if not name.startswith('agent_memory') and name != 'sqlite_sequence':
                    drop.append(name)
            # drop non-memory content tables (FTS shadows drop with their virtual table? keep FTS shadows of memory by prefix)
            keep_prefix = ('agent_memory',)
            drop = [n for n in drop if not n.startswith(keep_prefix)]
            for n in drop:
                try: cur.execute('DROP TABLE IF EXISTS "' + n + '"')
                except Exception as e:
                    print('  [WARN] drop', n, str(e)[:80], flush=True)
            con.commit()
            try:
                cur.execute('VACUUM')
                con.commit()
            except Exception as e:
                print('  [WARN] memory vacuum', str(e)[:100], flush=True)
            con.close()
            mbytes = os.path.getsize(t2)
            mparts, mok = (1, True) if mbytes <= 95 * 1024 * 1024 else (0, False)
            mbytes2, mparts2, mok = upload_object(t2, PREFIX + STAMP + '/agent-memory.db')
            print('agent-memory.db backup: ' + ('OK' if mok else 'FAIL') + ' (%d parts, %d bytes)' % (mparts2, mbytes2), flush=True)
            try: os.remove(t2)
            except Exception: pass
        return 0 if (sok and (mok or not MEMORY_BACKUP)) else 1
    except Exception as e:
        print('ERROR:', type(e).__name__, str(e)[:300]); return 1

if __name__ == '__main__':
    sys.exit(main())
