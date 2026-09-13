-- APPLY-QUEUE-2026-09-13.sql
-- Target: qnfo-audit (D1). Staged by qnfo-ops / ops-exec 2026-09-13.
-- qnfo-ops has NO D1 write path (ops_d1_query is SELECT-only). Nothing here has been run.
-- Every column name below was verified against pragma_table_info in this session.
-- Apply in order. Each section has a report query first; run it and read the output.
--
-- REVISION 2 (2026-09-13T14:15Z): §1.2's acceptance gate was a frozen row total
-- and had gone stale. §1/§3 header counts annotated with live values. §5 added.
-- §2 precondition re-verified: still 0, so §2.1 must run.
--
-- REVISION 3 (2026-09-13T14:22Z): §5/E1 SUPERSEDED - the code fix landed in repo
-- main while this audit was running (v1.1.6, single-module). Do NOT apply
-- Revision 2's E1 recommendation. §1 counts corrected a second time (concurrent
-- consolidation at 14:14Z). §5/E2 and §6 added. No D1 write occurred.

-- =====================================================================
-- §1  D14 - unify the split-brain issue ledgers.
--     issue_ledger has NO id column: its key is `fingerprint` (TEXT).
--     agent_issues.created_at is INTEGER epoch-ms; issue_ledger.first_seen
--     is ISO TEXT. Normalise both in the view.
--
--     THE COUNTS MOVED TWICE WHILE THIS FILE WAS BEING WRITTEN. That is the
--     point of §1.2, so every reading is kept:
--       staging (2026-09-13 AM): agent_issues 12 open / issue_ledger 303 open
--       14:12Z:                  agent_issues  3 open / issue_ledger  88 open
--       14:19Z:                  agent_issues 11 open / issue_ledger   7 open
--     At ~14:14-14:15Z a concurrent fleet process resolved 81 ledger rows
--     (issue_ledger resolved 237 -> 318; 183 resolved today) AND filed 11 new
--     agent_issues (ids 691-701, created_at epoch-ms 1789308851000-1789308925000
--     = 2026-09-13T14:14:11Z - 14:15:25Z). The split-brain did not disappear; it
--     was consolidated in the ledger->issues direction. Any hard-coded backlog
--     figure in this fleet is wrong within minutes.
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
--     Revision 1 said "must return >= 303 (the ledger alone), i.e. 12 + 303 =
--     315 rows". Both operands were staging-session values. Within one session
--     the true total went 315 -> 91 -> 18, so the old gate reads as a FAILURE on
--     a fix that worked. Accept by construction instead: the view must
--     reproduce both base counts exactly. Expected: mismatch = 0 on both rows.
--     VERIFIED 2026-09-13T14:19Z by emulating the view body in a CTE against the
--     live tables: agent_issues base 11 / view 11 / mismatch 0; issue_ledger
--     base 7 / view 7 / mismatch 0. The body compiles and the gate holds at 18
--     rows as well as at 91.
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
--     framing is no longer accurate. The defect is unchanged: 22/22 continuing
--     rows already hold length(response) > 0, i.e. `response` is written before
--     the terminal status, so any reader of that column must check `status`
--     first.
--     PREFERRED FIX IS WORKER-SIDE: write `response` and the terminal status in
--     one statement, and add a `terminal_at` column. The data-side reaper below
--     is a fallback and is deliberately left COMMENTED OUT - marking a
--     chain-midpoint row succeeded can corrupt chain bookkeeping if a successor
--     was spawned.
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
--        SEE §5/E2 - now evidenced as an hourly unbounded retry loop.
--     W4 probe coverage 12/55 -> 55/55 via service bindings.
--     W8 gateway capacity / unsatisfiable 24h [gw-fail] auto-close predicate.
--     W9 one autonomy/kill-switch evaluator (currently split across
--        governance_kernel.autonomy_boundary, fleet_deploy_state, autonomy_scores).
-- =====================================================================

-- =====================================================================
-- §5  LIVE-VERIFIED ERROR / WARNING / STALE-WORKER CENSUS
--     Read 2026-09-13T14:04-14:22Z from qnfo-audit via ops_d1_query, plus
--     qnfo-ops fleet_status / ops_issue_run, and the QNFO/qnfo-workers and
--     QNFO/qnfo-ops repos. Nothing in §5 has been remediated by this queue.
-- =====================================================================

-- E1 (HARD ERROR) qnfo-observability redeploy 1.1.3 -> 1.1.4 fails.
--    PRIMARY EVIDENCE, not inference:
--      fleet_deploys id=76, 2026-09-13 14:04:01, ok=0, 1.1.3 -> 1.1.4,
--      source_path 'r2:qnfo-canonical/qnfo-observability.js',
--      note HTTP 400 code 10021 "No such module \"fleet.js\". imported from
--      \"worker.js\"". self_heal_actions id=1405 mirrors it (drift, failed).
--    ROOT CAUSE: the control plane deploys from a single R2 key, and one key
--    cannot carry two modules. v1.1.4 was MULTI-MODULE (worker.js + ./fleet.js).
--    The repo was never at fault: fleet.js exists and its 55 names were diffed
--    against service_registry's 55 (exact match, 0 duplicates, 0 diffs).
--    qnfo-observability was the only fleet worker with a sibling module, so the
--    failure recurred hourly.
--
--    ** STATUS: SUPERSEDED - ALREADY FIXED IN REPO MAIN, 2026-09-13 **
--    qnfo-workers/main/qnfo-observability/worker.js is now v1.1.6 (37,386 B,
--    sha c72736a82865c4ea4c1027ef67e62ea0f05b9850). It inlines the 55-name
--    FLEET array and deletes the import; its own header cites fleet_deploys
--    id 76 as the trigger. Re-read AFTER the fix was announced - the earlier
--    read of the same path showed v1.1.4 at 29,719 B with the import present,
--    so the change landed DURING this session. Revision 2 of this file
--    recommended "inline the array into worker.js". DO NOT APPLY THAT - it is
--    done. The only remaining action is to refresh the stale canonical object
--    r2:qnfo-canonical/qnfo-observability.js (still 1.1.4). This endpoint
--    cannot: r2_put is bound to qnfo-releases / qnfo-audit / qnfo-backups /
--    qnfo-skills, NOT qnfo-canonical. Note QNFO/qnfo-workers has ZERO pull
--    requests (GitHub API state=all returned []), so there is no PR channel;
--    fixes land on main directly.

-- E2 (HARD ERROR, unbounded retry) personal-companion is being downgraded every
--    hour. fleet_deploys rows 68,70,71,72,73,74: from_sha v1.1.0 to to_sha
--    1.0.0, ok=0, identical HTTP 400 code 10021 "Workflow GenerationFlow must be
--    exported or a script_name must be specified", at 08:01:23, 09:01:23,
--    10:01:24, 11:01:23, 12:01:24, 13:01:23 - six consecutive hours, no backoff.
--    In the same window single-module workers deployed cleanly (qnfo-backlog-exec
--    1.2.6->1.2.7 at 08:01:43 and 1.2.7->1.2.8 at 14:02:44; qnfo-social
--    0.5.2->0.5.3 at 07:04:34), which isolates the fault to module topology /
--    workflow export rather than to the deployer as a whole. The canonical
--    artefact would DOWNGRADE a live v1.1.0 to 1.0.0 if it ever succeeded - that
--    is the more serious half of this row.

-- E3 (HARD ERROR) qnfo-cloud-ops canonical artefact is invalid JS (SyntaxError
--    at worker.js:1:2), reported as 25 consecutive hourly redeploy failures.
--    Filed independently as agent_issues 691/695 during this session; NOT
--    independently verified here. Do not treat as confirmed by this queue.

-- W1 (PERSISTENT WARNING, ~31 h) qnfo-observability ingest + digest are dead.
--      trace_ingest_state.last_key = workers_trace/20260910/
--        20260910T101640Z_20260910T101725Z_a05671da.log.gz
--        -> ingest cursor frozen since 2026-09-10T10:17Z (~3.2 days).
--      cloud_ops_events kind='fleet-observability-digest' n=34, newest
--        2026-09-12T06:58:50Z (~31 h) against cron '17 * * * *'.
--      integration_state newest row 2026-09-11T14:17:37Z.
--      alerts: 'WATCH:trace-stall: threshold breached' every ~3 h since
--        2026-09-10, status='err', never cleared.
--      fleet_runs id=486 systems-watch-hourly 2026-09-13T14:09:04Z: 8 SQL steps,
--        every one rows=0 - the watch probes empty because the producer stopped.
--        The alert is a symptom; the producer is the defect.
--      INTERACTION WITH E1: the v1.1.5 false-clean fix and the v1.1.6
--        single-module fix both sit undeployed behind the canonical key, so this
--        warning cannot clear until the canonical is refreshed.

-- W2 (DRIFT: 14 version-format detects, 4 staleCanon) non-semver
--    `fabric-20260910` cohort - deployed VERSION is not X.Y.Z, so the strict
--    HUB-VERSIONING-1 comparator cannot reconcile it and parks each entry:
--      qnfo-qwav (fabric-20260910 -> 2.1.0), qnfo-paper-indexer
--      (-> 2.2.0+scheduled-daily), qnfo-lifecycle
--      (-> 1.6.1-memory-maintain-fixed), qnfo-email (-> 0.3.4-glm53),
--      qnfo-ddocs-indexer (-> 1.0.0+server-side), qnfo-archive
--      (-> 1.2.0+cors-fixed), qnfo-agent-orchestrator (-> v1.0.0).
--    Also non-semver: qnfo-memory-mcp '2024-11-05', qnfo-agent-ws '2025-11-25',
--    qnfo-gateway '3.5.3-quarantine-filter'.
--    CROSS-ATTRIBUTION SUSPECT: 'qnfo-email ... -> 0.3.4-glm53' carries
--    qnfo-email-orchestrator's version string. Treat that row as a comparator
--    defect until proven otherwise, not as an email defect.
--    self_heal_actions totals: version-format detected 184 / healed 410; drift
--    deferred 228 / failed 26; health-ver deferred 228 / resolved 97.
--    "deferred" is not "fixed": 228 drift + 228 health-ver entries are parked.
--    CAVEAT: both fleet_drift_report and self_heal_actions are written by the
--    same fleet-control comparator, so W2 is single-source. If that comparator is
--    wrong (the qnfo-email row suggests it can be), the whole cohort is suspect
--    in the same direction.

-- W3 (COVERAGE GAP) fleet_heartbeat holds ONE row (qnfo-lifecycle,
--    2026-09-13T14:01:15Z, ok=1). 54 of 55 workers emit no heartbeat.
--    freshness_guard calls the signal "fresh" (age 0.3 h) because it tests only
--    the newest row - a single writer makes the whole fleet look alive.
--    Corroborated independently as agent_issues 701.

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
--        qnfo-fleet-dashboard (4), calendar-api (1), personal-api (2) - newest
--        seen_at 2026-09-11T05:17Z, none cleared.
--      integration_state (2026-09-11T14:17Z) still reports fleet_size=80.

-- W5 (MISCLASSIFIED STALENESS) freshness_guard marks a signal 'idle' rather than
--    'stale' when its mode is 'event', so age is not alerted:
--      pipeline_status: max_ts 2026-09-06T20:46:01Z, age 160.5 h vs threshold
--        24 h -> status 'idle'. 6.7 days stale, no alert raised.
--      outreach: age 268.3 h vs 72 h -> 'idle' (expected until the 2026-09-15
--        activation; listed only to show the rule).
--      handoffs: status 'unknown', checked_at 2026-09-11T16:46Z - the checker
--        itself has not run for ~2 days.

-- W6 (ALERT TEXT WAS FALSE - the finding was later filed correctly) alerts
--    id=1113/1109/1105 read "INTAKE-STALL escalated -> agent_issues dup: 496
--    proposals stuck new", repeated hourly. Live idea_proposals at 14:0xZ:
--    triaged_hold 543, triaged_accepted 14, ensemble-registered 1, new 0 - ZERO
--    new proposals. The real intake imbalance is one table over: signals new=110
--    vs consumed=152 (newest 'new' 2026-09-13T06:01Z). The stale alert text
--    still needs fixing at its source, but the substantive finding was filed
--    correctly and independently as agent_issues 699, which states the accurate
--    figure (543 parked triaged_hold) and adds two causes this census did not
--    find: watchdog target 404 and a self-blocked dedupe.

-- W7 (EXECUTOR CANNOT REACH THE OPEN BACKLOG) ops_issue_run confirm=true ran at
--    2026-09-13T14:09Z (qnfo-backlog-exec 1.2.8): processed=3, closed=0,
--    escalated=0, rechecked=3, and all three rows returned note="no probe target"
--    (ids 677, 687, 688). The drain can only close health-availability rows;
--    zenodo-publish and research-pipeline categories have no probe, so the open
--    backlog cannot drain itself. Underneath this, issue_ledger carries a
--    self-heal row 'tool ops_issue_run failing x42 (168h no recovery)'
--    (fingerprint selfheal:8a93970c, occurrences 27, last_seen
--    2026-09-13T14:15:04Z) - i.e. the same tool is recorded as persistently
--    failing while the call above returned HTTP 200 with a full payload. One of
--    the two is wrong; unresolved. The "no probe target" outcome is the likeliest
--    reconciliation (task-level failure counted as tool failure), but that is a
--    hypothesis, not a measurement.

-- W8 (STALE ISSUE PREMISE) issue 677 says version_queue id=18 has been "in error
--    since 2026-09-13 05:21:30". Live: version_queue has 17 rows, min id 1 max
--    id 18; id=18 is status='publishing' (2.0.1 -> 2.0.2, doi
--    10.5281/zenodo.22732639) with updated_at 2026-09-13T14:11:17Z, and
--    SELECT COUNT(*) WHERE status='error' returns 0. The rearm path the issue
--    text predicted ("purge-fix drain may auto-rearm after 2h") fired while this
--    audit was running - the row was observed changing state between two queries.
--    The issue should be closed, not rechecked.

-- W9 (CRON BOOKKEEPING) fleet_crons has 6 rows: demo-venue-radar-daily
--    (enabled=0, demo residue) and two Monday crons whose last_fired is a
--    Thursday - bench-arc-weekly ('0 8 * * 1', last_fired 2026-09-10T12:29:57Z)
--    and report-card-weekly-cron ('30 6 * * 1', last_fired 2026-09-10T12:32:57Z).
--    2026-09-10 is a Thursday (verified); the Monday before was 2026-09-07 and
--    next_fire is correctly 2026-09-14. Both last_fired values are registration
--    artefacts, not scheduled fires - so no Monday fire is actually evidenced.

-- W10 (SELF-MONITORING NOISE) issue_ledger open rows include AUTO-SWEEP entries
--    about this endpoint's own tools, unresolved: coe:4bcc7a2d 'AUTO-SWEEP:
--    ops_d1_query' 528 occurrences (first_seen 2026-09-04T06:16:48Z, last_seen
--    2026-09-13T12:21:29Z); coe:aac65ff3 'run_code' 61; coe:b8c324fc
--    'vectorize_query' 7. The ops_d1_query row is reproducible: the read guard
--    rejects inherently bounded introspection such as `SELECT name FROM
--    pragma_table_info('x')` with "add LIMIT n (aggregate exempt)", and it also
--    rejects a WITH ... UNION ALL ... of scalar subqueries. It fired three times
--    during this session. 528 hits on a guard that fires on correct queries
--    buries the real ones.

-- =====================================================================
-- §6  CROSS-CHECK: what the fleet's own consolidation filed at 14:14Z
--     A concurrent process opened agent_issues 691-701 while this census was
--     being written. Overlap with §5 is noted; items this census MISSED are
--     marked NEW. §5 is corroboration, not the source of record.
--       691 DEPLOY-CANONICAL-CORRUPT  r2:qnfo-canonical/qnfo-cloud-ops.js is
--           invalid JS at worker.js:1:2, 25 consecutive hourly failures   NEW
--       692 DEPLOY-HEALER-NO-BACKOFF  51 of 76 fleet_deploys rows are unbounded
--           hourly retries of 2 permanently-failing targets              ~E1/E2
--       693 WORKER-HEALTH-FALSE-530   worker-health reports qnfo-ai /
--           personal-api HTTP 530 code 1016 while service bindings prove 200;
--           recurrence of closed #356                                    NEW
--       694 OBSERVABILITY-MULTIMODULE-CANONICAL  = §5/E1 (same root cause)
--       695 DEPLOY-BLOCKER qnfo-cloud-ops  = 691, filed twice
--       696 DEPLOY-BLOCKER qnfo-observability  canonical stuck at 1.1.4 while
--           repo fix v1.1.6 is single-module = §5/E1 + the canonical-resync gap
--       697 ALERT-STORM qnfo-pipeline-ops  802 critical alerts, fix undeployed NEW
--       698 AI-GATEWAY request-shape defects  20,402 HTTP 400s across three
--           models  ~ this census read ai_gateway_failures but under-counted
--       699 INTAKE-STALL  543 triaged_hold, watchdog target 404, dedupe
--           self-blocked  ~W6, and it is the CORRECT version of W6
--       700 DEPLOY-LOOP downgrade  personal-companion canonical 1.0.0 over live
--           v1.1.0  = §5/E2
--       701 FLEET-MONITORING blind spot  43 of 55 unprobed + a second
--           unreconciled roster  ~W3/W4
--     LESSON: the fleet found E1, E2, W3, W4 and W6 on its own, and found E3,
--     the 530 false-negative, the alert storm and the 20k gateway 400s which this
--     census missed. A single-endpoint census is not the audit.

-- §7 NOTE - what was executed and what was deliberately not.
--   EXECUTED this session: one ops_issue_run (confirm=true, W7 above); one
--   telemetry_analyze (24 h: scanned 11, persistent 0, recovered 7, filed 0,
--   alreadyOpen 3); github_file_write to this file (Revision 2, commit
--   b4b0642fb961ce32b2b31450ff186c7a872422dc, then this Revision 3).
--   NOT EXECUTED: §1-§3 (no D1 write path on this endpoint); the E1 code fix
--   (already done upstream in repo main - see §5/E1); the canonical re-sync that
--   E1 now needs (no R2 binding to qnfo-canonical); E3 and the items marked NEW
--   in §6 (not verified here).
