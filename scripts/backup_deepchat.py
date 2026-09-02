#!/usr/bin/env python3
"""backup_deepchat.py — DeepChat state backup gate (permanent, 2026-09-01).
Snapshots Roaming DeepChat settings/DB + canonical prompt stores and uploads to
R2 qnfo-backups/deepchat/YYYY/MM/. Prints 'BACKUP OK' and exits 0 on success.
Canonical: QNFO/qnfo-ops/scripts/backup_deepchat.py (mirrored .deepchat/scripts)
"""
import os, sys, json, time, io, shutil, urllib.request, urllib.error, sqlite3

TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', '')
ACCT = 'edb167b78c9fb901ea5bca3ce58ccc4b'
BUCKET = 'qnfo-backups'
ROAM = r'C:/Users/LENOVO/AppData/Roaming/DeepChat'
HOMEDEEP = r'C:/Users/LENOVO/.deepchat'
STAMP = time.strftime('%Y%m%d-%H%M%S')
PREFIX = 'deepchat/' + time.strftime('%Y/%m') + '/'

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
    # DB snapshot (sqlite backup) -> temp then upload
    db_src = os.path.join(ROAM, 'app_db', 'agent.db')
    db_tmp = os.path.join(os.environ.get('TEMP', 'C:/Users/LENOVO/AppData/Local/Temp'), 'agent-snapshot-' + STAMP + '.db')
    try:
        src_conn = sqlite3.connect(db_src, timeout=30)
        dst_conn = sqlite3.connect(db_tmp)
        src_conn.backup(dst_conn)
        dst_conn.close(); src_conn.close()
        key = PREFIX + STAMP + '/agent.db'
        with open(db_tmp, 'rb') as f:
            data = f.read()
        if upload(key, data):
            uploaded.append('agent.db (' + str(round(len(data)/1048576,1)) + ' MB)')
        else:
            errors.append('agent.db: upload failed')
        try: os.remove(db_tmp)
        except Exception: pass
    except Exception as e:
        errors.append('agent.db: ' + type(e).__name__ + ' ' + str(e)[:150])
    if errors:
        for e in errors:
            print('[BACKUP-ERROR] ' + e)
        print('BACKUP ERROR: ' + str(len(errors)) + ' failure(s)')
        return 1
    print('BACKUP OK (' + str(len(uploaded)) + ' files -> R2 ' + BUCKET + '/' + PREFIX + STAMP + '): ' + ', '.join(uploaded))
    return 0

if __name__ == '__main__':
    sys.exit(main())
