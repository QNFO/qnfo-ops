#!/usr/bin/env python3
"""adversarial-guard.py — permanent adversarial-reasoning sweep gate (2026-09-05).

PRECONDITION:
  - customPrompts-canonical.json exists at CANON_JSON (the 11 CMD templates).
  - skills live under SKILLS_DIR with one SKILL.md each.
  - ADVERSARIAL-REASONING-1 (system-prompt v4.17) requires the canonical
    one-line '- ADVERSARIAL:' block in every CMD template and every SKILL.md.

INVARIANT (enforced):
  - Every one of the 11 CMD templates carries the ADVERSARIAL marker AND at
    least one anti-sycophancy token (flatter/disagree) AND at least one
    anti-confirmation token (disconfirm/steelman) AND a failure-mode token.
  - Every SKILL.md carries the ADVERSARIAL marker.

POSTCONDITION:
  - Exit 0 iff the invariant holds across all surfaces; else exit 1 and list
    the failing surfaces. Prints one summary line per checked surface.

WHY (justification): the v4.17 gate says the canonical form 'now lives in all
11 CMD templates + all skills' and is 'swept by scripts/adversarial-guard.py'.
That sweep script was referenced but never written (dangling internal anchor,
INTERNAL-ANCHOR-DANGLING-1 class). This is it.

SCOPE: device-bound local file read (permitted local op — the prompt stores are
local mirrors of the canonical repo). Canonical: QNFO/qnfo-ops/scripts/
adversarial-guard.py (mirror .deepchat/scripts/adversarial-guard.py).
Run on every ops cycle and after ANY prompt/skill dual-write (PROMPT-PARITY-1).
"""
import json, os, sys

CANON_JSON = r"C:/Users/LENOVO/.deepchat/scripts/customPrompts-canonical.json"
SKILLS_DIR = r"C:/Users/LENOVO/.deepchat/skills"
EXPECTED_TEMPLATES = 11

def check_text(c, label):
    c_l = (c or "").lower()
    has_adv = "adversarial" in c_l
    has_syc = any(t in c_l for t in ("flatter", "disagree", "defer"))
    has_conf = any(t in c_l for t in ("disconfirm", "steelman"))
    has_fm = "failure mode" in c_l
    ok = has_adv and has_syc and has_conf and has_fm
    detail = f"adv={has_adv} syc={has_syc} conf={has_conf} fm={has_fm}"
    print(f"{'PASS' if ok else 'FAIL'}  {label}  [{detail}]")
    return ok

def main():
    fails = []
    # 1. CMD templates
    if not os.path.exists(CANON_JSON):
        print(f"FAIL  canonical json missing: {CANON_JSON}")
        return 1
    templates = json.load(open(CANON_JSON, encoding="utf-8"))
    if len(templates) != EXPECTED_TEMPLATES:
        print(f"FAIL  template count {len(templates)} != {EXPECTED_TEMPLATES}")
        return 1
    for t in templates:
        label = f"tpl:{t.get('name')}"
        if not check_text(t.get("content", ""), label):
            fails.append(label)
    # 2. Skills
    if not os.path.isdir(SKILLS_DIR):
        print(f"FAIL  skills dir missing: {SKILLS_DIR}")
        return 1
    n_skills = 0
    for d in sorted(os.listdir(SKILLS_DIR)):
        f = os.path.join(SKILLS_DIR, d, "SKILL.md")
        if not os.path.isfile(f):
            continue
        n_skills += 1
        try:
            body = open(f, encoding="utf-8", errors="replace").read()
        except Exception as e:
            print(f"FAIL  skill:{d}  read error {e}")
            fails.append(f"skill:{d}")
            continue
        if "adversarial" not in body.lower():
            print(f"FAIL  skill:{d}  (no ADVERSARIAL marker)")
            fails.append(f"skill:{d}")
        else:
            print(f"PASS  skill:{d}")
    print(f"--- templates={len(templates)} skills={n_skills} fails={len(fails)} ---")
    if fails:
        print("FAIL surfaces: " + ", ".join(fails))
        return 1
    print("ADVERSARIAL-GUARD: PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
