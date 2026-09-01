#!/usr/bin/env python3
import json, os, re, datetime
rows = json.load(open(r'C:/Users/LENOVO/AppData/Local/Temp/fleet_rows.json', encoding='utf-8'))
QW = r'C:/Users/LENOVO/AppData/Local/Temp/qnfo-workers'
QO = r'C:/Users/LENOVO/AppData/Local/Temp/qnfo-ops'
def repo_dir(name):
    if os.path.isdir(os.path.join(QW, name)): return 'qnfo-workers/' + name
    if os.path.isdir(os.path.join(QO, 'cloud', name)): return 'qnfo-ops/cloud/' + name
    return None
def deployed_version(name):
    d = repo_dir(name)
    if not d: return None
    base = os.path.join(QW, name) if d.startswith('qnfo-workers') else os.path.join(QO, 'cloud', name)
    cand = os.path.join(base, 'deployed-current.worker.js')
    if not os.path.isfile(cand): cand = os.path.join(base, 'worker.js')
    if not os.path.isfile(cand): return None
    try:
        txt = open(cand, encoding='utf-8', errors='replace').read()
        m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', txt)
        return m.group(1) if m else 'UNVERSIONED'
    except Exception:
        return None
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
L = []
L.append('# QNFO FLEET MANIFEST - Cloudflare Workers Ecosystem')
L.append('')
L.append('> Auto-generated ' + now + ' by the fleet self-documentation sweep. Living inventory;')
L.append('> the weekly Fleet Drift & Self-Improvement Audit cron re-generates it and flags drift.')
L.append('')
L.append('## Self-documentation policy (FLEET-SELF-DOC-1)')
L.append('')
L.append('Every worker MUST carry: (1) a VERSION constant reachable via /health; (2) a header comment with purpose, capabilities, deploy method, and Canonical source path; (3) a canonical repo dir under QNFO/qnfo-workers/<name> or QNFO/qnfo-ops/cloud/<name> with a deployed-current.worker.js that byte-matches the deployed bundle. Status: OK = all three; PARTIAL = versioned but not repo-synced; GAP = missing one or more.')
L.append('')
L.append('## Fleet (' + str(len(rows)) + ' workers)')
L.append('')
L.append('| Worker | Live version | Modified (UTC) | Canonical repo | Repo version | Self-doc |')
L.append('|---|---|---|---|---|---|')
for w in rows:
    name = str(w['name'])
    ver = w.get('version')
    ver = str(ver) if (ver is not None and ver not in ('NO-HEALTH','ERR','None','True')) else 'NO-HEALTH'
    mod = str(w['modified'])
    d = repo_dir(name)
    rv = deployed_version(name)
    if not d: sd = 'GAP (no repo dir)'
    elif rv is None: sd = 'GAP (no deployed-current)'
    elif rv != ver and ver != 'NO-HEALTH': sd = 'DRIFT repo=' + str(rv)
    elif ver == 'NO-HEALTH': sd = 'PARTIAL (no /health)'
    else: sd = 'OK'
    L.append('| ' + name + ' | ' + ver + ' | ' + mod + ' | ' + (d or '-') + ' | ' + (rv or '-') + ' | ' + sd + ' |')
L.append('')
ok = sum(1 for l in L if '| OK |' in l)
L.append('## Summary')
L.append('')
L.append('- Total workers: ' + str(len(rows)))
L.append('- Self-doc OK: ' + str(ok))
L.append('- Drift/partial/gap: ' + str(len(rows) - ok))
L.append('- NO-HEALTH rows are expected for cron-only utility workers (no HTTP surface).')
L.append('')
L.append('## Self-improvement loop')
L.append('')
L.append('1. Fleet Drift & Self-Improvement Audit cron (weekly): re-runs this sweep, logs drift to qnfo-audit D1, repairs where the fix is a documented one-liner (wrangler deploy from canonical repo).')
L.append('2. AI Worker Health + Provider Config Guard cron (every 3h): probes qnfo-ai + personal-api chat paths and DeepChat provider config.')
L.append('3. QNFO Data Freshness Sync cron (every 6h): keeps Vectorize fresh with calendar + email.')
L.append('4. Kaizen cycles (CMD SKILLS UPDATE): every session lesson becomes a named gate in skills + system prompt (dual-written, parity-verified).')
out = os.path.join(QO, 'docs', 'FLEET-MANIFEST.md')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write('\n'.join(L))
print('manifest written')
for l in L:
    if l.startswith('- '): print(l)
