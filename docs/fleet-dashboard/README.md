# Fleet Operations Dashboard (local snapshot)

Generated 2026-09-07 by the DeepChat fleet-dashboard builder.

## Files
- fleet-dashboard.html  — self-contained at-a-glance page (open in any browser). Sections: (1) CF scheduled fleet 48 workers — crons, next fires (Europe/Amsterdam), fleet_error_state flags; (2) pipeline/workflow evidence cards from qnfo-audit/outreach/living D1; (3) Windows scheduled tasks (last result codes); (4) DeepChat local cron registry (canonical 5, guard PASS); (5) public endpoint probe reality; (6) gaps.
- snapshot-2026-09-07.json — machine-readable evidence (window.__SNAPSHOT__ embedded in the html).

## Data sources
- CF schedule registry: qnfo-fleet-dashboard worker REGISTRY captured 2026-09-07T17:42Z from the CF Workers API (48 scheduled workers). Sibling worker is NOT yet live/routed (see gaps).
- Evidence: D1 qnfo-audit (fleet_error_state, scheduler_state, agent_issues, ai_gateway_failures, ops_ai_log, deployment_history, task_dod_register, errata_queue, version_queue, paper_revision_log, audit_workers, ai_model_health), qnfo-outreach (pipeline_state, sent_log), living-paper (papers), Windows Task Scheduler (schtasks), DeepChat local cron registry (cronjob list+history), scheduler-guard.py.

## Refresh
Re-run the collector in DeepChat (needs cronjob + D1 + schtasks access) — sources are device/API-bound; there is no standalone CLI yet. Long-term: the sibling qnfo-fleet-dashboard worker should serve this page in-cloud once routed/bound (register coordination).

## Errors surfaced on 2026-09-07 (action needed)
- CF fleet_error_state: personal-api(2), qnfo-container-executor(3), calendar-api(1), job-market-watch(1).
- Windows: QNFO_FS_Maintenance_Daily=1 (09-07 15:54), QNFO_Obsidian_Sync=3 (09-07 19:53), QNFO_Obsidian_Start=-2147020576.
- DeepChat local cron 6e91c844 (C: disk free guard) last fire failed (exec error).
- deployment_history stale since 2026-09-04.
