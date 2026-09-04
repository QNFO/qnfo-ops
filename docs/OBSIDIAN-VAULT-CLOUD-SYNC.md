# Obsidian Vault → Cloud Sync & Knowledge Integration (2026-09-04)

Status: LIVE (v1.0). Claim/evidence/confidence/status per FRAMEWORK-DOGFOOD-1.

## Topology
```
D:\Obsidian (local vault, canonical, user writes in Obsidian)
   │  obsidian_sync.py  (rclone copy --update, push-only, every 15 min + logon)
   ▼
R2 bucket d-drive  →  prefix obsidian/  (1:1 keys, vault-root-relative, durable superset archive)
   │  personal-life-indexer (env.DDRIVE binding; registry dedupe by path|size|modified)
   ▼
personal-life D1 (files/chunks/notes) + Vectorize personal-life  →  personal twin RAG (personal-api)

Obsidian-writer worker  →  R2 bucket obsidian-vault  →  notes/v1/YYYY/MM/YYYY-MM-DD/_slug-DATE.md
(fleet-generated research briefs = separate upstream plane; not mirrored down by this sync)
```

## Conventions
- Key prefix: `obsidian/<path-relative-to-vault-root>` (matches historical indexer rows in
  personal-life D1 files.path LIKE 'obsidian/%', 1,631 rows verified 2026-09-04).
- Push-only (no --delete): local vault canonical; R2 keeps deleted files = archive semantics.
- Filters (scripts/obsidian-sync-filters.txt): desktop.ini, Thumbs.db, *.tmp, .DS_Store, .git/**,
  .rclone-bisync/**, .obsidian/workspace*.json, obsidian-releases-*.zip.
- Path-naming note: local vault uses numeric day folders (notes/v1/2026/09/02); the obsidian-writer
  upstream uses date-string folders (notes/v1/2026/09/2026-09-02). Both trees coexist; consumers
  read content, not folder style.

## Mechanisms (verified 2026-09-04)
- scripts/obsidian_sync.py — python driver: msvcrt lock (overlap guard), rclone copy --update
  --filter-from, exit codes + run log to .deepchat/logs/obsidian-sync-run.log.
- Windows Task Scheduler QNFO_Obsidian_Sync — every 15 min, interactive only, pythonw.
- HKCU Run key 'Obsidian' = "C:\Program Files\Obsidian\Obsidian.exe" (logon autostart beside DeepChat).
- Stale artifacts disabled: obsidian_bisync.cmd / obsidian_bisync_run.vbs renamed *.disabled-2026-09-04
  (bisync targets obsidian-vault with a different convention; never ran; superseded by d-drive push).
- pl_phase_obsidian.vbs references missing email-composer/scripts/obsidian_to_r2.py — OUT OF SCOPE here
  (personal-life phase suite), flagged as drift to fix by its owner (email-composer skill scripts moved).

## Gap / blindspot assessment (2026-09-04)
1. REASONABLE? Yes as one-way mirror; two-way (bisync) is NOT advised: obsidian-writer deletes+recreates
   upstream notes (delete-then-create), and folder conventions differ — bisync would create duplicates
   and conflict churn. Push-only + upstream-writer plane = no collision domain.
2. PRIVACY: vault content (incl. personal notes) is plaintext in private R2. Personal KB already lives in
   CF (personal-life D1/VZ), so posture is consistent; if pvt/ grows sensitive data, add rclone crypt
   remote (client-side encryption) — owner: user decision, date: none (open).
3. INGEST LATENCY: personal-life-indexer is cron-sliced (400/300 per run) and dedupes by signature;
   first index of ~1,200 newly mirrored files completes over subsequent slices. QNFO-side vault ingest
   (research notes → qnfo-notes/qwav stores) has NO consumer yet — recommended next worker: vault-kb-bridge
   binding d-drive, classify per-note (personal|research|both), write qnfo-notes VZ + qnfo-audit rows.
4. DELETION RECOVERY: R2 archive means accidental local deletion still recoverable from bucket; local
   .trash is disabled in Obsidian config (trashOption:none) — consider enabling Obsidian trash.
5. COST: ~500 MB upload one-time + deltas; R2 free-tier ample; Class B ops negligible at 15-min cadence.
6. CONFLICT: --update = mtime/size no-clobber; simultaneous local edit + upstream overwrite of same leaf
   name under different folders can diverge — leaf names are unique by convention (_slug-DATE / epoch-ms).
