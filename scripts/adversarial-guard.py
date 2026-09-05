#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adversarial-guard.py - permanent guard enforcing ADVERSARIAL-REASONING-1 across agent surfaces.

Read-only. Exit 0 = all core surfaces carry the adversarial-reasoning block; 1 = violations.
Canonical: QNFO/qnfo-ops/scripts/adversarial-guard.py (mirror at .deepchat/scripts).
"""
import os, sys, json, glob, re

SKILLS_ROOT = r"C:/Users/LENOVO/Documents/GitHub/qnfo-skills"
TEMPLATES = os.path.join(SKILLS_ROOT, "prompt-stores", "customPrompts.json")
SYSPROMPT = r"C:/Users/LENOVO/.deepchat/system-prompt-v2.7.md"
WORKERS_ROOT = r"C:/Users/LENOVO/Documents/GitHub/qnfo-workers"
SKILL_MARKER = "## Adversarial reasoning (ADVERSARIAL-REASONING-1)"
TEMPLATE_MARKER = "- ADVERSARIAL:"
SYS_MARKER = "ADVERSARIAL-REASONING-1"
CORE_WORKERS = ["qnfo-ai", "qnfo-ops", "personal-api", "agent-orchestrator",
                "qnfo-ipatent", "qnfo-intent-orchestrator"]

violations = []
def check(ok, label):
    print(("PASS " if ok else "FAIL ") + label)
    if not ok:
        violations.append(label)

skill_md = glob.glob(os.path.join(SKILLS_ROOT, "*", "SKILL.md"))
missing = [p for p in skill_md if SKILL_MARKER not in open(p, encoding="utf-8").read()]
check(not missing, f"skills: {len(skill_md)} SKILL.md, {len(missing)} missing ADVERSARIAL section"
      + ("" if not missing else " -> " + ", ".join(os.path.basename(os.path.dirname(p)) for p in missing[:8])))

tpl = json.load(open(TEMPLATES, encoding="utf-8"))
tmiss = [e.get("name") for e in tpl if TEMPLATE_MARKER not in (e.get("content") or "")]
check(not tmiss, f"templates: {len(tpl)} entries, {len(tmiss)} missing ADVERSARIAL line"
      + ("" if not tmiss else " -> " + ", ".join(tmiss)))

check(SYS_MARKER in open(SYSPROMPT, encoding="utf-8").read(), "system prompt carries ADVERSARIAL-REASONING-1")

for w in CORE_WORKERS:
    p = os.path.join(WORKERS_ROOT, w, "worker.js")
    ok = os.path.exists(p) and SYS_MARKER in open(p, encoding="utf-8").read()
    check(ok, f"worker {w} carries ADVERSARIAL-REASONING-1")

if "--workers" in sys.argv:
    print("\n== full worker sweep ==")
    workers = sorted(os.path.basename(os.path.dirname(p))
                     for p in glob.glob(os.path.join(WORKERS_ROOT, "*", "worker.js")))
    for w in workers:
        p = os.path.join(WORKERS_ROOT, w, "worker.js")
        s = open(p, encoding="utf-8").read()
        has_surface = (bool(re.search(r'role\s*:\s*["\x27]system', s)) or 'SYSTEM_PROMPT' in s
                       or 'DEFAULT_SYSTEM_PROMPT' in s or 'OPS_SYSTEM_PROMPT' in s or 'systemPrompt' in s)
        if not has_surface:
            continue
        status = "PASS" if SYS_MARKER in s else "GAP "
        print(f"  {status} {w}")

print()
if violations:
    print(f"RESULT: {len(violations)} violation(s)")
    sys.exit(1)
print("RESULT: all core adversarial-reasoning surfaces pass")
sys.exit(0)
