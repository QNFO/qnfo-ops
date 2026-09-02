#!/usr/bin/env python3
"""backup_agentdb_chunked.py — agent.db backup via chunked R2 REST upload (permanent, 2026-09-02).
Closes the agent.db gap (v1.1 skip path): the R2 v4 REST single-PUT cap is ~100 MB
(HTTP 413 above it) and wrangler carries a ~300 MiB object cap, so a >100 MB agent.db
is uploaded as <=90 MB parts + a manifest, using ONLY the existing CLOUDFLARE_API_TOKEN.
Restore = concatenate parts in order (manifest carries sha256 + sizes).
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

def upload(key, data):
    url = f'https://api.cloudflare.com/client/v4/accounts/{ACCT}/r2/buckets/{BUCKET}/objects/{key}'
    req = urllib.request.Request(url, method='PUT', data=data, headers={
        'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/octet-stream',
        'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode('utf-8')).get('success', False)

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
        size = os.path.getsize(tmp)
        parts = (size + CHUNK - 1) // CHUNK
        if parts <= 1 and size <= 95 * 1024 * 1024:
            # small enough for a single REST PUT - reuse plain key
            with open(tmp, 'rb') as f:
                data = f.read()
            key = PREFIX + STAMP + '/agent.db'
            ok = upload(key, data)
            print('agent.db single upload: ' + ('OK' if ok else 'FAIL'))
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
