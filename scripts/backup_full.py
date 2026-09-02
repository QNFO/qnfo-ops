
#!/usr/bin/env python3
"""backup_full.py - one-command FULL DeepChat backup (permanent, 2026-09-02).
Runs backup_deepchat.py (5 config-state files) then backup_agentdb_chunked.py
(agent.db >95MB -> chunked parts + manifest). Prints combined verdict:
  BACKUP OK (FULL) / BACKUP PARTIAL / BACKUP ERROR. Exit 0 only when BOTH succeed.
Canonical: QNFO/qnfo-ops/scripts/backup_full.py (mirror .deepchat/scripts).
Usage: python backup_full.py
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, 'backup_deepchat.py')
DB = os.path.join(HERE, 'backup_agentdb_chunked.py')

def main():
    results = []
    for label, script in (('config', CFG), ('agent.db', DB)):
        t0 = time.time()
        print('[backup_full] running ' + label + ' (' + os.path.basename(script) + ') ...', flush=True)
        try:
            r = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=1800)
            out = (r.stdout or '') + (('\n' + r.stderr) if r.stderr else '')
            ok = r.returncode == 0
            results.append((label, ok, out.strip()))
            print('[backup_full] ' + label + ' exit=' + str(r.returncode) + ' in ' + str(int(time.time()-t0)) + 's', flush=True)
            tail = '\n'.join(out.strip().splitlines()[-6:])
            if tail:
                print('  ' + tail.replace('\n', '\n  '), flush=True)
        except Exception as e:
            results.append((label, False, str(e)))
    ok_all = all(ok for _, ok, _ in results)
    if ok_all:
        print('BACKUP OK (FULL): config-state files + agent.db chunked backup both uploaded to R2 qnfo-backups.')
        return 0
    print('BACKUP PARTIAL/ERROR: full backup incomplete - see child output above.')
    return 1 if not any(ok for _, ok, _ in results) else 2

if __name__ == '__main__':
    sys.exit(main())
