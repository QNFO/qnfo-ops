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
L = ['# QNFO FLEET MANIFEST — Cloudflare Workers Ecosystem', '',
     '> Auto-generated ' + now + ' by the fleet self-documentation sweep.',
     '> Living inventory; weekly Fleet Drift cron (42b1988c) re-generates and flags drift.',
     '', '## Self-documentation policy (FLEET-SELF-DOC-1)', '',
     'Every worker MUST carry: (1) VERSION reachable via /health; (2) header with purpose/canonical source; (3) canonical repo deployed-current.worker.js. Status: OK = all; PARTIAL = versioned not repo-synced; GAP = missing one or more.',
     '', '## Fleet (' + str(len(rows)) + ' workers)', '',
     '| Worker | Live version | Modified (UTC) | Canonical repo | Repo version | Self-doc |', '|---|---|---|---|---|---|']
for w in rows:
    name = str(w['name']); ver = w.get('version'); mod = str(w['modified'])
    d = repo_dir(name); rv = deployed_version(name)
    if ver is None: ver = 'NO-HEALTH'
    else: ver = str(ver)
    if ver in ('NO-HEALTH', 'ERR', 'None', 'True'): ver = 'NO-HEALTH'
    if not d: sd = 'GAP (no repo dir)'
    elif rv is None: sd = 'PARTIAL (no repo deployed-current)'
    elif rv != ver and ver != 'NO-HEALTH': sd = 'DRIFT repo=' + str(rv)
    elif ver == 'NO-HEALTH': sd = 'GAP (no /health)'
    else: sd = 'OK'
    L.append('| ' + name + ' | ' + ver + ' | ' + mod + ' | ' + (d or '-') + ' | ' + (rv or '-') + ' | ' + sd + ' |')
L += ['', '## Summary', '']
ok = sum(1 for l in L if '| OK |' in l)
drift = sum(1 for l in L if '| DRIFT ' in l)
gap = sum(1 for l in L if ('| GAP ' in l) or ('| PARTIAL ' in l))
L += ['- Total workers: ' + str(len(rows)), '- Self-doc OK: ' + str(ok), '- Drift: ' + str(drift), '- GAP/PARTIAL: ' + str(gap),
      '', '## Self-improvement loop', '',
      '1. Fleet Drift & Self-Improvement Audit cron (weekly): re-runs sweep, logs drift, repairs via wrangler redeploy.',
      '2. AI Worker Health + Provider Config Guard cron (every 3h): probes qnfo-ai + personal-api chat paths.',
      '3. QNFO Data Freshness Sync cron (every 6h): calendar + email to Vectorize.',
      '4. Kaizen cycles: every lesson becomes a named gate, dual-written. OPS-SELF-DOC.md is the master index.']
out = os.path.join(QO, 'docs', 'FLEET-MANIFEST.md')
open(out, 'w', encoding='utf-8').write('\n'.join(L))
print('manifest regenerated OK=%d drift=%d gap=%d' % (ok, drift, gap))
