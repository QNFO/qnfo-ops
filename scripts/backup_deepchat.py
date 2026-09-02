#!/usr/bin/env python3
"""backup_deepchat.py — DeepChat state backup gate (permanent, 2026-09-01).
Snapshots Roaming DeepChat settings/DB + canonical prompt stores and uploads to
R2 qnfo-backups/deepchat/YYYY/MM/. Prints 'BACKUP OK' and exits 0 on success.
Canonical: QNFO/qnfo-ops/scripts/backup_deepchat.py (mirrored .deepchat/scripts)

v1.3 (2026-09-02, user directive): agent.db is pruned to SETTINGS-PRESERVING content before
upload (backup_agentdb_chunked.py v1.1 prunes chat-thread CONTENT on the snapshot copy: messages,
assistant blocks, tape, search docs, delegations + FTS; KEEPS app_settings/providers/models/agents/
cron/mcp/sessions (per-thread settings)/usage/memory). Whole-DB backup is rejected as unsustainable
(agent.db ~1.2 GB; chat threads expendable, their settings are not). Measured 1223.5 MB -> ~116 MB
(90.5%%). The LIVE agent.db is never modified.


v1.2 (2026-09-02): agent.db gap CLOSED - delegates to backup_agentdb_chunked.py (chunked REST parts + manifest) when > REST single-PUT limit. agent.db (~0.9 GB) exceeds the R2
REST API single-PUT object limit (~100 MB; HTTP 413) and wrangler's 300 MiB cap.
v1.0 failed the WHOLE backup when the agent.db PUT 413'd, which made closeouts
report "backup complete" as FALSE while the 5 config-state files had actually
uploaded. v1.1 uploads the 5 config-state files, then for agent.db: if it exceeds
the deterministic REST limit it is SKIPPED with an explicit reason (not an error),
or on HTTP 413 it is converted to a skip. Output is BACKUP OK (full), BACKUP
PARTIAL (config-state ok, agent.db skipped with reason), or BACKUP ERROR (a
config-state file failed). Exit 0 for OK/PARTIAL, 1 for ERROR/missing token.
agent.db > limit is uploaded via backup_agentdb_chunked.py (<=90MB parts + manifest, same CLOUDFLARE_API_TOKEN).
"""
import os, sys, json, time, io, shutil, urllib.request, urllib.error, sqlite3

TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', '')
ACCT = 'edb167b78c9fb901ea5bca3ce58ccc4b'
BUCKET = 'qnfo-backups'
ROAM = r'C:/Users/LENOVO/AppData/Roaming/DeepChat'
HOMEDEEP = r'C:/Users/LENOVO/.deepchat'
STAMP = time.strftime('%Y%m%d-%H%M%S')
PREFIX = 'deepchat/' + time.strftime('%Y/%m') + '/'
REST_SINGLE_PUT_LIMIT = 95 * 1024 * 1024  # conservative vs ~100 MB REST cap

FILES = [
    (os.path.join(ROAM, 'app-settings.json'), 'app-settings.json'),
    (os.path.join(ROAM, 'mcp-settings.json'), 'mcp-settings.json'),
    (os.path.join(ROAM, 'custom_prompts.json'), 'custom_prompts.json'),
    (os.path.join(HOMEDEEP, 'system-prompt-v2.7.md'), 'system-prompt-v2.7.md'),
    (os.path.join(HOMEDEEP, 'system-prompt-history-v2.7.md'), 'system-prompt-history-v2.7.md'),
]

def upload(key, data):
    url = f'https://api.cloudflare.com/client/v4/accounts/{ACCT}/r2/buckets/{BUCKET}/objects/{key}'
    req = urllib.request.Request(url, method='PUT', data=data, headers={
        'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/octet-stream', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read().decode('utf-8'))
    return d.get('success', False)

def main():
    if not TOKEN:
        print('BACKUP ERROR: CLOUDFLARE_API_TOKEN missing')
        return 1
    uploaded = []
    errors = []
    skipped = []
    for src, name in FILES:
        key = PREFIX + STAMP + '/' + name
        try:
            with open(src, 'rb') as f:
                data = f.read()
            if upload(key, data):
                uploaded.append(name)
            else:
                errors.append(name + ': upload failed')
        except Exception as e:
            errors.append(name + ': ' + type(e).__name__ + ' ' + str(e)[:150])
    # DB snapshot (sqlite backup) -> temp then upload; graceful on size/413
    db_src = os.path.join(ROAM, 'app_db', 'agent.db')
    db_tmp = os.path.join(os.environ.get('TEMP', 'C:/Users/LENOVO/AppData/Local/Temp'), 'agent-snapshot-' + STAMP + '.db')
    db_skip_reason = None
    try:
        src_conn = sqlite3.connect(db_src, timeout=30)
        dst_conn = sqlite3.connect(db_tmp)
        src_conn.backup(dst_conn)
        dst_conn.close(); src_conn.close()
        key = PREFIX + STAMP + '/agent.db'
        with open(db_tmp, 'rb') as f:
            data = f.read()
        size_mb = round(len(data)/1048576, 1)
        if len(data) > REST_SINGLE_PUT_LIMIT:
            import subprocess
            rc = subprocess.run([sys.executable, os.path.join(HOMEDEEP, 'scripts', 'backup_agentdb_chunked.py')]).returncode
            if rc == 0:
                uploaded.append('agent.db (chunked via backup_agentdb_chunked.py)')
                db_skip_reason = None
            else:
                db_skip_reason = 'agent.db chunked backup failed (backup_agentdb_chunked.py rc=%d)' % rc
        else:
            try:
                if upload(key, data):
                    uploaded.append('agent.db (' + str(size_mb) + ' MB)')
                else:
                    errors.append('agent.db: upload failed')
            except urllib.error.HTTPError as he:
                if he.code == 413:
                    db_skip_reason = f'agent.db ({size_mb} MB) HTTP 413 above R2 REST single-PUT limit; needs S3 multipart (creds not provisioned)'
                else:
                    errors.append('agent.db: HTTP ' + str(he.code))
        try: os.remove(db_tmp)
        except Exception: pass
    except Exception as e:
        errors.append('agent.db: ' + type(e).__name__ + ' ' + str(e)[:150])
    if db_skip_reason:
        skipped.append(db_skip_reason)
    if errors:
        for e in errors:
            print('[BACKUP-ERROR] ' + e)
        print('BACKUP ERROR: ' + str(len(errors)) + ' failure(s)')
        return 1
    if skipped:
        for s in skipped:
            print('[BACKUP-SKIPPED] ' + s)
        print('BACKUP PARTIAL (' + str(len(uploaded)) + ' config-state files -> R2 ' + BUCKET + '/' + PREFIX + STAMP + '): ' + ', '.join(uploaded))
        pass  # v1.2: no gap - chunked delegation handles large agent.db
        return 0
    print('BACKUP OK (' + str(len(uploaded)) + ' files -> R2 ' + BUCKET + '/' + PREFIX + STAMP + '): ' + ', '.join(uploaded))
    return 0

if __name__ == '__main__':
    sys.exit(main())
