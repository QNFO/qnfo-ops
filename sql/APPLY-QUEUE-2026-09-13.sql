-- APPLY-QUEUE-2026-09-13.sql
-- Target: qnfo-audit (D1). Staged by qnfo-ops / ops-exec 2026-09-13.
-- qnfo-ops has NO D1 write path (ops_d1_query is SELECT-only). Nothing here has been run.
-- Every column name below was verified against pragma_table_info in this session.
-- Apply in order. Each section has a report query first; run it and read the output.
--
-- REVISION 2 (2026-09-13T14:15Z): §1.2's acceptance gate was a frozen row total
-- and had gone stale (see §1.2). §1/§3 header counts annotated with live values.
-- §5 added (live-verified error/warning/stale-worker census). §2 precondition
-- re-verified: still 0, so §2.1 must run.

-- =====================================================================
-- §1  D14 - unify the split-brain issue ledgers.
--     STAGING COUNT (2026-09-13 AM): agent_issues 12 open vs
--     issue_ledger 303 open; ratio ~25x, violates axiom A3.
--     LIVE COUNT (2026-09-13T14:12Z): agent_issues 3 open vs
--     issue_ledger 88 open; ratio ~29x. The ledger did not shrink by repair -
--     217 of its rows moved to status='resolved'. The split-brain and the A3
--     violation are unchanged; only the magnitudes moved. Do not read the
--     staging numbers as current.
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

-- §1.2 acceptance - MUST NOT be a frozen row total.
--     Revision 1 said "must return >= 303 (the ledger alone), i.e.
--     12 + 303 = 315 rows". Both operands were staging-session values.
--     Live 2026-09-13T14:12Z the view returns 91 rows (3 + 88), so the old
--     gate reads as a FAILURE on a fix that worked. Accept by construction
--     instead: the view must reproduce both base counts exactly.
--     Expected result: mismatch = 0 on both rows.
SELECT 'agent_issues' AS store,
       (SELECT COUNT(*) FROM agent_issues WHERE status = 'open') AS base,
       (SELECT COUNT(*) FROM unified_open_issues WHERE store = 'agent_issues') AS view,
       (SELECT COUNT(*) FROM agent_issues WHERE status = 'open')
         - (SELECT COUNT(*) FROM unified_open_issues WHERE store = 'agent_issues') AS mismatch
UNION ALL
SELECT 'issue_ledger',
       (SELECT COUNT(*) FROM issue_ledger WHERE status = 'open'),
       (SELECT COUNT(*) FROM unified_open_issues WHERE store = 'issue_ledger'),
       (SELECT COUNT(*) FROM issue_ledger WHERE status = 'open')
         - (SELECT COUNT(*) FROM unified_open_issues WHERE store = 'issue_ledger');

-- §1.2b optional shape check
-- SELECT * FROM unified_open_issues ORDER BY opened_at DESC LIMIT 20;

-- §1.3 follow-up (not in this queue): point ops_issues_list / backlog_status at
-- unified_open_issues. Until that ships, every backlog figure this fleet reports
-- undercounts by the size of the ledger store.

-- =====================================================================
-- §2  D16 - restore the SAI time series. report_card_history currently
--     has 1 row with sai = NULL, grade = NULL; the writer
--     (fleet_runs id=111, 'report-card-weekly') failed with
--     "table report_card_history has no column named source", so the
--     trigger value was stuffed into signals_json instead.
--     Live columns: id, ts, sai, grade, scores_json, signals_json.
--     RE-VERIFIED 2026-09-13T14:1xZ: still 1 row (ts 2026-09-10T12:33:04Z,
--     sai NULL, grade NULL) and §2.0 still returns 0. D16 is UNFIXED.
-- =====================================================================

-- §2.0 report first - if this returns 1, §2.1 is a no-op and MUST be skipped
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
-- §3  D17 - ops_jobs never terminates.
--     STAGING COUNT (2026-09-13 AM): 40 succeeded / 28 continuing /
--     8 failed / 4 running.
--     LIVE COUNT (2026-09-13T14:08Z): 96 succeeded / 19 continuing /
--     8 failed / 6 running. Re-measured 14:10Z: continuing 22 - the cohort
--     MOVES (partly this endpoint's own session traffic), so the "frozen ~6h"
--     framing is no longer accurate. The defect is unchanged: 22/22
--     continuing rows already hold length(response) > 0, i.e. `response` is
--     written before the terminal status, so any reader of that column must
--     check `status` first.
--     PREFERRED FIX IS WORKER-SIDE: write `response` and the terminal status
--     in one statement, and add a `terminal_at` column. The data-side reaper
--     below is a fallback and is deliberately left COMMENTED OUT - marking a
--     chain-midpoint row succeeded can corrupt chain bookkeeping if a
--     successor was spawned.
-- =====================================================================

-- §3.0 report first: candidates (response present, no recent update)
SELECT status, COUNT(*) AS n, MAX(updated_at) AS newest_update
FROM ops_jobs
WHERE length(response) > 0
GROUP BY status;

-- §3.1 fallback reaper - DO NOT RUN without reading §3.0 and checking
--     each row's chain successor. Uncomment deliberately.
-- UPDATE ops_jobs
-- SET status = 'succeeded', updated_at = datetime('now')
-- WHERE status = 'continuing'
--   AND length(response) > 0
--   AND updated_at < datetime('now', '-1 hour');

-- =====================================================================
-- §4  Not in this queue (documented only, needs worker source or a deploy):
--     W1 deployer comparator (non-semver VERSION vs heal gate) - source is
--        75,875 B, over the 32,768-char read cap; cannot be patched from here.
--     W1(b) personal-companion upload - 'Workflow GenerationFlow must be
--        exported or a script_name must be specified'; canonical 62,666 B.
--     W4 probe coverage 12/55 -> 55/55 via service bindings.
--     W8 gateway capacity / unsatisfiable 24h [gw-fail] auto-close predicate.
--     W9 one autonomy/kill-switch evaluator (currently split across
--        governance_kernel.autonomy_boundary, fleet_deploy_state, autonomy_scores).
-- =====================================================================

-- =====================================================================
-- §5  LIVE-VERIFIED ERROR / WARNING / STALE-WORKER CENSUS
--     Read 2026-09-13T14:04-14:15Z from qnfo-audit via ops_d1_query,
--     plus qnfo-ops fleet_status and one ops_issue_run (confirm=true).
--     Nothing in §5 has been remediated by this queue.
-- =====================================================================

-- E1 (HARD ERROR, unresolved) qnfo-observability redeploy 1.1.3 -> 1.1.4 fails.
--    self_heal_actions id=1405, ts 2026-09-13 14:04:01, status=failed:
--      HTTP 400 {"code":10021,"message":"Uncaught Error: No such module
--      \"fleet.js\". imported from \"worker.js\""}
--    Repo state was CHECKED, not assumed: qnfo-workers/main/qnfo-observability/
--    holds worker.js (29,719 B, `import { FLEET } from './fleet.js';`) and
--    fleet.js (2,596 B). fleet.js's 55 names were diffed against
--    service_registry's 55 names: exact match, 0 duplicates, 0 diffs.
--    => The module is missing from the CANONICAL STORE, not the repo. The
--       canonical deploy path ships a single worker.js, so any worker with a
--       sibling ES module can never be healed by it. qnfo-observability is the
--       only such worker, so the failure recurs hourly (drift status=failed 26
--       rows; fleet-execute failed 25 rows).
--    FIX (NOT applied from this endpoint - see the note at the end of §5):
--      (a) inline the 55-name array into worker.js and delete the import, so
--          the canonical single-file artefact is self-contained; OR
--      (b) make the canonical store carry the module graph.

-- W1 (PERSISTENT WARNING, ~31 h) qnfo-observability ingest + digest are dead.
--      trace_ingest_state.last_key = workers_trace/20260910/
--        20260910T101640Z_20260910T101725Z_a05671da.log.gz
--        -> ingest cursor frozen since 2026-09-10T10:17Z (~3.2 days).
--      cloud_ops_events kind='fleet-observability-digest' n=34,
--        newest 2026-09-12T06:58:50Z (~31 h) against cron '17 * * * *'.
--      integration_state newest row 2026-09-11T14:17:37Z.
--      alerts: 'WATCH:trace-stall: threshold breached' every ~3 h since
--        2026-09-10, status='err', never cleared.
--      fleet_runs id=486 systems-watch-hourly 2026-09-13T14:09:04Z: 8 SQL
--        steps, every one rows=0 - the watch probes empty because the
--        producer stopped. The alert is a symptom; the producer is the defect.

-- W2 (DRIFT: 14 version-format detects, 4 staleCanon) non-semver
--    `fabric-20260910` cohort - deployed VERSION is not X.Y.Z, so the strict
--    HUB-VERSIONING-1 comparator cannot reconcile it and parks each entry:
--      qnfo-qwav (fabric-20260910 -> 2.1.0), qnfo-paper-indexer
--      (-> 2.2.0+scheduled-daily), qnfo-lifecycle
--      (-> 1.6.1-memory-maintain-fixed), qnfo-email (-> 0.3.4-glm53),
--      qnfo-ddocs-indexer (-> 1.0.0+server-side), qnfo-archive
--      (-> 1.2.0+cors-fixed), qnfo-agent-orchestrator (-> v1.0.0).
--    Also non-semver: qnfo-memory-mcp '2024-11-05', qnfo-agent-ws
--    '2025-11-25', qnfo-gateway '3.5.3-quarantine-filter'.
--    CROSS-ATTRIBUTION SUSPECT: 'qnfo-email ... -> 0.3.4-glm53' carries
--    qnfo-email-orchestrator's version string. Treat that row as a comparator
--    defect until proven otherwise, not as an email defect.
--    self_heal_actions totals: version-format detected 184 / healed 410;
--    drift deferred 228 / failed 26; health-ver deferred 228 / resolved 97.
--    "deferred" is not "fixed": 228 drift + 228 health-ver entries are parked.

-- W3 (COVERAGE GAP) fleet_heartbeat holds ONE row (qnfo-lifecycle,
--    2026-09-13T14:01:15Z, ok=1). 54 of 55 workers emit no heartbeat.
--    freshness_guard calls the signal "fresh" (age 0.3 h) because it tests
--    only the newest row - a single writer makes the whole fleet look alive.

-- W4 (STALE CONTROL-PLANE ROWS for retired workers) The fleet consolidated
--    81 -> 55 on 2026-09-12. These tables were not pruned:
--      fleet_logpush_sweep: qnfo-blank-audit, qnfo-auditor, qnfo-analytics,
--        qnfo-arxiv-radar (status 'on', all ts 2026-09-10 07:5x).
--      fleet_deploy_state: scanerr:jnl-reviser, scanerr:jnl-zenodo,
--        scanerr:job-market-watch, scanerr:personal-life-indexer,
--        scanerr:personal-life-maintain, scanerr:personal-life-search
--        (+ 'stale-canon' on obsidian-writer, osf-integrity-check,
--        personal-life-maintain).
--      fleet_error_state: qnfo-container-executor (3), job-market-watch (9),
--        qnfo-fleet-advisor (3), qnfo-citation-watch (2), __unknown__ (2),
--        qnfo-fleet-dashboard (4), calendar-api (1), personal-api (2) -
--        newest seen_at 2026-09-11T05:17Z, none cleared.
--      integration_state (2026-09-11T14:17Z) still reports fleet_size=80.

-- W5 (MISCLASSIFIED STALENESS) freshness_guard marks a signal 'idle' rather
--    than 'stale' when its mode is 'event', so age is not alerted:
--      pipeline_status: max_ts 2026-09-06T20:46:01Z, age 160.5 h vs threshold
--        24 h -> status 'idle'. 6.7 days stale, no alert raised.
--      outreach: age 268.3 h vs 72 h -> 'idle' (expected until the 2026-09-15
--        activation; listed only to show the rule).
--      handoffs: status 'unknown', checked_at 2026-09-11T16:46Z - the checker
--        itself has not run for ~2 days.

-- W6 (ALERT TEXT IS FALSE) alerts id=1113/1109/1105 read "INTAKE-STALL
--    escalated -> agent_issues dup: 496 proposals stuck new", repeated hourly.
--    Live idea_proposals: triaged_hold 543, triaged_accepted 14,
--    ensemble-registered 1, new 0. There are ZERO new proposals. The real
--    intake imbalance is one table over: signals new=110 vs consumed=152
--    (newest 'new' 2026-09-13T06:01Z). An alert that names a table and a count
--    that no longer hold trains operators to ignore the channel.

-- W7 (EXECUTOR CANNOT REACH THE OPEN BACKLOG) ops_issue_run confirm=true ran at
--    2026-09-13T14:09Z (qnfo-backlog-exec 1.2.8): processed=3, closed=0,
--    escalated=0, rechecked=3, and all three rows returned
--    note="no probe target" (ids 677, 687, 688). The drain can only close
--    health-availability rows; zenodo-publish and research-pipeline categories
--    have no probe, so the open backlog cannot drain itself.

-- W8 (STALE ISSUE PREMISE) issue 677 says version_queue id=18 has been "in
--    error since 2026-09-13 05:21:30". Live: version_queue has 17 rows,
--    min id 1 max id 18; id=18 is status='publishing' (2.0.1 -> 2.0.2, doi
--    10.5281/zenodo.22732639) with updated_at 2026-09-13T14:11:17Z, and
--    SELECT COUNT(*) WHERE status='error' returns 0. The rearm path the issue
--    text predicted ("purge-fix drain may auto-rearm after 2h") fired while
--    this audit was running. The issue should be closed, not rechecked.

-- W9 (CRON BOOKKEEPING) fleet_crons has 6 rows: demo-venue-radar-daily
--    (enabled=0, demo residue) and two Monday crons whose last_fired is a
--    Thursday - bench-arc-weekly ('0 8 * * 1', last_fired 2026-09-10T12:29:57Z)
--    and report-card-weekly-cron ('30 6 * * 1', last_fired 2026-09-10T12:32:57Z).
--    2026-09-10 is a Thursday; the Monday before was 2026-09-07 and next_fire
--    is correctly 2026-09-14. Both last_fired values are registration
--    artefacts, not scheduled fires - so no Monday fire is actually evidenced.

-- W10 (SELF-MONITORING BACKLOG) issue_ledger open rows include three
--    AUTO-SWEEP entries about this endpoint's own tools, unresolved:
--      coe:4bcc7a2d 'AUTO-SWEEP: ops_d1_query' - 528 occurrences,
--        first_seen 2026-09-04T06:16:48Z, last_seen 2026-09-13T12:21:29Z.
--      coe:aac65ff3 'AUTO-SWEEP: run_code' - 61 occurrences.
--      coe:b8c324fc 'AUTO-SWEEP: vectorize_query' - 7 occurrences.
--    The ops_d1_query row is reproducible: the read guard rejects inherently
--    bounded introspection such as `SELECT name FROM pragma_table_info('x')`
--    with "add LIMIT n (aggregate exempt)". 528 hits on a guard that fires on
--    correct queries is noise that buries real ones.

-- §5 NOTE - what was executed and what was deliberately not.
--   EXECUTED this session: one ops_issue_run (confirm=true, W7 above) and one
--   telemetry_analyze (24 h: scanned 11, persistent 0, recovered 7, filed 0,
--   alreadyOpen 3). No D1 write path exists on this endpoint, so no §1-§3
--   statement above was run.
--   NOT EXECUTED, deliberately: E1 fix (a) is a whole-file rewrite of a
--   29,719-byte canonical worker. This endpoint will not emit a 30 KB file it
--   cannot re-read for byte-equality, because a silent drift would be deployed
--   fleet-wide as the fleet's own observability layer. E1 needs either a
--   branch+PR with a reviewed diff, or fix (b) in the deploy path.
