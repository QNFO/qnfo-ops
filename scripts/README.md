# qnfo-ops/scripts — Ops Toolbox (bootstrapped 2026-08-05)

Per the thin-client mandate (KIF-32), reusable ops scripts live here in git and
NEVER persist on the local filesystem. The local machine is a thin client: any
script that exists ONLY locally is a violation.

## Lifecycle (HOW)

1. Need a script? -> Check this dir first.
2. Not here? -> Write it, commit to qnfo-ops/scripts/ (same-turn commit), then
   clone-to-TEMP to run.
3. Here? -> Clone to %%TEMP%%, run, DELETE the clone (same turn). Use the
   `\\?\` + rmtree pattern to clear read-only git pack files, or chmod-sweep first.
4. One-shot logic? -> Write to %%TEMP%% and let it die. NEVER commit throwaways.

## Rules

- Skill-bound scripts (e.g. bloat-cleanup's 26 scripts) live in QNFO/qnfo-skills
  under skills/<name>/scripts/ — NOT here. This dir is for CROSS-CUTTING ops tools
  that no single skill owns.
- qnfo-ops is governance (AUDT/HAND/PLCY/SKIL/WBS). scripts/ is the executable
  toolbox layer added per the thin-client mandate.
- Every session ends with: no local-only files (bloat-cleanup pre-closeout scan).
