-- APPLY-QUEUE-2026-09-13.sql
-- Target: qnfo-audit (D1). Staged by qnfo-ops / ops-exec 2026-09-13.
-- qnfo-ops has NO D1 write path (ops_d1_query is SELECT-only). Nothing here has been run.
-- Every column name below was verified against pragma_table_info in this session.
-- Apply in order. Each section has a report query first; run it and read the output.

-- =====================================================================
-- §1  D14 — unify the split-brain issue ledgers (agent_issues 12 open
--     vs issue_ledger 303 open; ratio ~25x, violates axiom A3).
--     issue_ledger has NO id column: its key is `fingerprint` (TEXT).
--     agent_issues.created_at is INTEGER epoch-ms; issue_ledger.first_seen
--     is ISO TEXT. Normalise both in the view.
-- =====================================================================

-- §1.0 report first
SELECT 'agent_issues' AS store, COUNT(*) AS open_rows FROM agent_issues WHERE status = 'open'
UNION ALL
SELECT 'issue_ledger', COUNT(*) FROM issue_ledger WHERE status = 'open';

-- §1.1 the unification view (idempotent)
CREATE VIEW IF NOT EXISTS unified_open_issues AS
SELECT 'agent_issues'            AS store,
       CAST(id AS TEXT)          AS ref,
       priority                  AS prio,
       title                     AS title,
       status                    AS status,
       CASE WHEN typeof(created_at) = 'integer'
            THEN strftime('%Y-%m-%dT%H:%M:%SZ', created_at / 1000.0)
            ELSE created_at END  AS opened_at
FROM agent_issues
WHERE status = 'open'
UNION ALL
SELECT 'issue_ledger',
       fingerprint,
       level,
       title,
       status,
       first_seen
FROM issue_ledger
WHERE status = 'open';

-- §1.2 acceptance: must return >= 303 (the ledger alone), i.e. 12 + 303 = 315 rows
-- SELECT store, COUNT(*) FROM unified_open_issues GROUP BY store;
-- SELECT * FROM unified_open_issues ORDER BY opened_at DESC LIMIT 20;

-- §1.3 follow-up (not in this queue): point ops_issues_list / backlog_status at
-- unified_open_issues. Until that ships, every backlog figure this fleet reports
-- undercounts by the size of the ledger store.

-- =====================================================================
-- §2  D16 — restore the SAI time series. report_card_history currently
--     has 1 row with sai = NULL, grade = NULL; the writer
--     (fleet_runs id=111, 'report-card-weekly') failed with
--     "table report_card_history has no column named source", so the
--     trigger value was stuffed into signals_json instead.
--     Live columns: id, ts, sai, grade, scores_json, signals_json.
-- =====================================================================

-- §2.0 report first — if this returns 1, §2.1 is a no-op and MUST be skipped
--     (ALTER TABLE ADD COLUMN is not idempotent in SQLite).
SELECT COUNT(*) AS has_source_column
FROM pragma_table_info('report_card_history')
WHERE name = 'source';

-- §2.1 add the column (run ONLY if §2.0 returned 0)
ALTER TABLE report_card_history ADD COLUMN source TEXT DEFAULT 'unknown';

-- §2.2 backfill from the JSON the trigger record already carries
UPDATE report_card_history
SET source = COALESCE(json_extract(signals_json, '$.source'), 'unknown')
WHERE source = 'unknown'
  AND signals_json IS NOT NULL
  AND json_valid(signals_json) = 1;

-- §2.3 acceptance
-- SELECT id, ts, sai, grade, source FROM report_card_history ORDER BY ts DESC LIMIT 10;
-- The 1 existing row must read source = 'cloud-weekly-cron-trigger'.

-- =====================================================================
-- §3  D17 — ops_jobs never terminates: 28 rows in 'continuing'
--     (40 succeeded / 28 continuing / 8 failed / 4 running) and every
--     continuing row already holds a non-empty response.
--     PREFERRED FIX IS WORKER-SIDE: write `response` and the terminal
--     status in one statement, and add a `terminal_at` column. The
--     data-side reaper below is a fallback and is deliberately left
--     COMMENTED OUT — marking a chain-midpoint row succeeded can
--     corrupt chain bookkeeping if a successor was spawned.
-- =====================================================================

-- §3.0 report first: candidates (response present, no recent update)
SELECT status, COUNT(*) AS n, MAX(updated_at) AS newest_update
FROM ops_jobs
WHERE length(response) > 0
GROUP BY status;

-- §3.1 fallback reaper — DO NOT RUN without reading §3.0 and checking
--     each row's chain successor. Uncomment deliberately.
-- UPDATE ops_jobs
-- SET status = 'succeeded', updated_at = datetime('now')
-- WHERE status = 'continuing'
--   AND length(response) > 0
--   AND updated_at < datetime('now', '-1 hour');

-- =====================================================================
-- §4  Not in this queue (documented only, needs worker source or a deploy):
--     W1 deployer comparator (non-semver VERSION vs heal gate) — source is
--        75,875 B, over the 32,768-char read cap; cannot be patched from here.
--     W1(b) personal-companion upload — 'Workflow GenerationFlow must be
--        exported or a script_name must be specified'; canonical 62,666 B.
--     W4 probe coverage 12/55 -> 55/55 via service bindings.
--     W8 gateway capacity / unsatisfiable 24h [gw-fail] auto-close predicate.
--     W9 one autonomy/kill-switch evaluator (currently split across
--        governance_kernel.autonomy_boundary, fleet_deploy_state, autonomy_scores).
-- =====================================================================
