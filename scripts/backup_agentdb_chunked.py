#!/usr/bin/env python3
"""backup_agentdb_chunked.py - agent.db backup via chunked R2 REST upload (permanent, 2026-09-02).
v1.1 (2026-09-02, user directive): SETTINGS-PRESERVING CHAT PRUNE before upload. The user
rejected whole-DB backup (agent.db ~1.2 GB): chat threads are ephemeral/expendable but the
settings/config state in them is not. Every snapshot now prunes chat-thread CONTENT tables
(messages, assistant blocks, tape, search docs, delegations) and clears their FTS indexes
BEFORE upload, keeping: app_settings, providers, provider_models, model_configs, agents,
cron_jobs, mcp_servers, deepchat_sessions (per-thread settings: system_prompt, temperature,
context_length, max_tokens), new_sessions, usage_stats, agent_memory (durable knowledge).
Measured: 1223.5 MB -> ~116 MB (10.5x), integrity_check ok. The LIVE agent.db is never
touched - pruning happens on the sqlite snapshot copy only. Restore = concatenate parts
in order (manifest carries sha256 + sizes) or single PUT when under the cap.
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
FTS_DELETE_ALL = ['deepchat_search_documents_fts']   # external-content FTS5 -> delete-all command
FTS_PLAIN_DELETE = ['deepchat_tape_search_fts']      # regular-content FTS5 -> DELETE FROM works

def upload(key, data):
    url = f'https://api.cloudflare.com/client/v4/accounts/{ACCT}/r2/buckets/{BUCKET}/objects/{key}'
    req = urllib.request.Request(url, method='PUT', data=data, headers={
        'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/octet-stream',
        'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode('utf-8')).get('success', False)

def prune_chats(db_path):
    """Delete chat-thread CONTENT on a snapshot copy; keep settings/session/memory tables."""
    con = sqlite3.connect(db_path, timeout=60)
    con.execute('PRAGMA busy_timeout=15000')
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r[0] for r in cur.fetchall()}
    removed = 0
    for t in PRUNE_TABLES:
        if t in names:
            try:
                cur.execute('DELETE FROM "' + t + '"')
                removed += cur.rowcount
            except Exception as e:
                print('  [PRUNE-WARN]', t, str(e)[:100], flush=True)
    # FTS: external-content tables use the delete-all special command; regular FTS uses DELETE FROM
    for t in FTS_DELETE_ALL:
        if t in names:
            try:
                cur.execute('INSERT INTO "' + t + '"("' + t + '") VALUES("delete-all")')
            except Exception as e:
                print('  [PRUNE-WARN] fts delete-all', t, str(e)[:100], flush=True)
    for t in FTS_PLAIN_DELETE:
        if t in names:
            try:
                cur.execute('DELETE FROM "' + t + '"')
            except Exception as e:
                print('  [PRUNE-WARN] fts delete', t, str(e)[:100], flush=True)
    con.commit()
    try:
        cur.execute('VACUUM')
    except Exception as e:
        print('  [PRUNE-WARN] vacuum', str(e)[:100], flush=True)
    con.commit(); con.close()
    return removed

def main():
    if not TOKEN:
        print('ERROR: CLOUDFLARE_API_TOKEN missing'); return 1
    db_src = os.path.join(ROAM, 'app_db', 'agent.db')
    tmp = os.path.join(os.environ.get('TEMP', 'C:/Users/LENOVO/AppData/Local/Temp'),
                       'agent-snapshot-' + STAMP + '.db')
    try:
        src = sqlite3.connect(db_src, timeout=60)
        dst = sqlite3.connect(tmp)
        src.backup(dst); dst.close(); src.close()
        before = os.path.getsize(tmp)
        removed = prune_chats(tmp)
        size = os.path.getsize(tmp)
        print('prune: removed %d chat rows, %d -> %d bytes (%.1f%% saved)' % (
            removed, before, size, (100.0 * (before - size) / before) if before else 0), flush=True)
        parts = (size + CHUNK - 1) // CHUNK
        if parts <= 1 and size <= 95 * 1024 * 1024:
            with open(tmp, 'rb') as f:
                data = f.read()
            key = PREFIX + STAMP + '/agent.db'
            ok = upload(key, data)
            print('agent.db single upload (pruned): ' + ('OK' if ok else 'FAIL'))
            return 0 if ok else 1
        keybase = PREFIX + STAMP + '/agent.db/'
        sha = hashlib.sha256()
        n = 0
        with open(tmp, 'rb') as f:
            while True:
                data = f.read(CHUNK)
                if not data:
                    break
                n += 1
                sha.update(data)
                ok = upload(keybase + 'part_%03d_of_%03d' % (n, parts), data)
                print('part %d/%d uploaded' % (n, parts), flush=True)
                if not ok:
                    print('ERROR uploading part %d' % n); return 1
        manifest = {
            'object': 'agent.db', 'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'bytes': size, 'parts': parts, 'chunk_bytes': CHUNK,
            'sha256': sha.hexdigest(),
            'prune': 'chat-thread content removed (settings/sessions/memory preserved)',
            'restore': 'cat part_*_of_%03d > agent.db' % parts,
            'note': 'R2 v4 REST multipart unavailable; concatenate parts in order to restore'}
        ok = upload(keybase + 'manifest.json', json.dumps(manifest).encode('utf-8'))
        if not ok:
            print('ERROR uploading manifest'); return 1
        print('agent.db chunked backup OK: %d parts, %d bytes, sha256 %s' % (parts, size, sha.hexdigest()))
        return 0
    finally:
        try: os.remove(tmp)
        except Exception: pass

if __name__ == '__main__':
    sys.exit(main())
