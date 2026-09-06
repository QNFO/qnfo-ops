# QNFO FLEET MANIFEST — Cloudflare Workers Ecosystem

> Auto-generated 2026-09-06 20:53 UTC by fleet-manifest-sweep.py v2.1 (self-contained enumeration + /health probes).
> Living inventory; weekly Fleet Drift cron (42b1988c) re-generates this file from live CF state - do NOT hand-edit;
> deploy history lives in qnfo-audit deployment_history + git log.

## Self-documentation policy (FLEET-SELF-DOC-1)

Every worker MUST carry: (1) VERSION reachable via /health; (2) header with purpose/canonical source;
(3) canonical repo deployed-current.worker.js. Status: OK = all; PARTIAL = versioned not repo-synced;
GAP = missing one or more. AUTH-GATED = /health behind auth (monitor must send bearer).

## Fleet (71 workers)

| Worker | Live version | Modified (UTC) | Canonical repo | Repo version | Self-doc |
|---|---|---|---|---|---|
| calendar-api | 0.3.0 | 2026-09-03 04:46:55 | qnfo-workers/calendar | 0.3.0 | OK |
| events-radar | 1.0.1 | 2026-09-02 11:14:48 | qnfo-workers/events-radar | 1.0.1 | OK |
| jnl-referee | 0.1.1 | 2026-09-06 20:52:04 | qnfo-workers/jnl-referee | 0.1.1 | OK |
| jnl-watch | 0.1.6 | 2026-09-06 11:58:02 | qnfo-workers/jnl-watch | 0.1.6 | OK |
| job-market-watch | NO-HEALTH | 2026-09-01 11:28:57 | - | - | GAP (no repo dir) |
| obsidian-writer | NO-HEALTH | 2026-09-01 11:11:34 | - | - | GAP (no repo dir) |
| osf-integrity-check | NO-VERSION | 2026-09-01 11:56:24 | - | - | GAP (no repo dir) |
| personal-api | v3.1.0 | 2026-09-05 20:47:36 | qnfo-workers/personal-api | v3.1.0 | OK |
| personal-events-radar | 1.2.4 | 2026-09-03 04:46:37 | qnfo-workers/personal-events-radar | 1.2.4 | OK |
| personal-life-indexer | v2.5-index-auth | 2026-08-20 17:19:11 | qnfo-workers/personal-life-indexer | - | PARTIAL (no repo deployed-current) |
| personal-life-maintain | NO-HEALTH | 2026-09-01 07:27:59 | - | - | GAP (no repo dir) |
| personal-life-search | v1.2.3-env-secret | 2026-08-28 09:48:43 | qnfo-workers/personal-life-search | - | PARTIAL (no repo deployed-current) |
| qnfo-agent-orchestrator | v1.0.0 | 2026-09-05 20:47:42 | qnfo-workers/agent-orchestrator | 1.0.0 | OK |
| qnfo-agent-ws | 1.3.9 | 2026-08-14 14:50:27 | - | - | GAP (no repo dir) |
| qnfo-ai | 5.21.1 | 2026-09-05 20:47:42 | qnfo-workers/qnfo-ai | 5.21.1 | OK |
| qnfo-ai-calibration | 1.1.2 | 2026-09-06 08:14:43 | qnfo-workers/qnfo-ai-calibration | 1.1.2 | OK |
| qnfo-ai-search | 1.0.2 | 2026-08-12 06:30:11 | qnfo-workers/qnfo-ai-search | 1.0.2 | OK |
| qnfo-analytics | NO-VERSION | 2026-09-05 20:19:58 | - | - | GAP (no repo dir) |
| qnfo-archive | 1.2-cors-fixed | 2026-07-30 12:05:58 | qnfo-workers/qnfo-archive | - | PARTIAL (no repo deployed-current) |
| qnfo-arxiv-radar | NO-HEALTH | 2026-09-01 18:02:45 | - | - | GAP (no repo dir) |
| qnfo-auditor | 1.1.7 | 2026-09-04 02:07:58 | qnfo-workers/qnfo-auditor | 1.1.7 | OK |
| qnfo-backlog-exec | 1.1.1 | 2026-09-02 18:31:50 | qnfo-workers/qnfo-backlog-exec | 1.1.1 | OK |
| qnfo-blank-audit | 1.1.0 | 2026-09-02 20:34:47 | qnfo-workers/qnfo-blank-audit | 1.1.0 | OK |
| qnfo-chat-canary | 1.0.2 | 2026-09-03 04:57:33 | qnfo-workers/qnfo-chat-canary | 1.0.2 | OK |
| qnfo-citation-watch | 1.0.0 | 2026-09-03 05:51:42 | qnfo-workers/qnfo-citation-watch | 1.0.0 | OK |
| qnfo-cloud-ops | 1.13.4 | 2026-09-06 07:50:13 | qnfo-workers/qnfo-cloud-ops | 1.13.4 | OK |
| qnfo-code-agent | 0.1.0 | 2026-09-06 11:29:16 | qnfo-workers/qnfo-code-agent | 0.1.0 | OK |
| qnfo-code-orchestrator | 0.1.1 | 2026-09-06 17:14:06 | qnfo-workers/qnfo-code-orchestrator | 0.1.1 | OK |
| qnfo-container-executor | 0.1.0 | 2026-09-06 17:05:45 | qnfo-ops/cloud/qnfo-container-executor | - | PARTIAL (no repo deployed-current) |
| qnfo-containers-pilot | 0.3.0 | 2026-09-06 17:04:37 | qnfo-workers/qnfo-containers-pilot | 0.3.0 | OK |
| qnfo-ddocs-indexer | v1.0-server-side | 2026-09-04 09:55:53 | qnfo-workers/qnfo-ddocs-indexer | UNVERSIONED | DRIFT repo=UNVERSIONED |
| qnfo-email | AUTH-GATED | 2026-08-31 21:22:10 | - | - | GAP (no repo dir) |
| qnfo-email-orchestrator | 0.3.3-p1-p1 | 2026-09-03 13:38:46 | qnfo-workers/qnfo-email-orchestrator | 0.3.3-p1-p1 | OK |
| qnfo-errata-orchestrator | 1.0.0 | 2026-09-02 21:47:31 | qnfo-workers/errata-orchestrator | 1.0.0 | OK |
| qnfo-errata-publish | 0.7.1-relid-fix | 2026-09-04 14:40:11 | qnfo-workers/qnfo-errata-publish | 0.7.1 | DRIFT repo=0.7.1 |
| qnfo-errata-respond | 0.4.1 | 2026-09-03 13:38:10 | qnfo-workers/qnfo-errata-respond | 0.4.1 | OK |
| qnfo-errata-watch | 0.2.1 | 2026-09-03 13:38:14 | qnfo-workers/qnfo-errata-watch | 0.2.1 | OK |
| qnfo-error-selfheal | 1.0.2 | 2026-09-06 20:50:21 | qnfo-workers/qnfo-error-selfheal | 1.0.2 | OK |
| qnfo-events | 1.1.0 | 2026-09-04 02:04:15 | qnfo-workers/qnfo-events | 1.1.0 | OK |
| qnfo-fleet-calibrator | 1.0.0 | 2026-09-04 05:10:58 | qnfo-workers/qnfo-fleet-calibrator | 1.0.0 | OK |
| qnfo-gateway | NO-HEALTH | 2026-09-03 18:23:45 | - | - | GAP (no repo dir) |
| qnfo-idea-factory | 2.7.3 | 2026-09-04 14:27:40 | qnfo-workers/qnfo-idea-factory | 2.7.3 | OK |
| qnfo-idea-miner | NO-HEALTH | 2026-09-03 13:37:06 | - | - | GAP (no repo dir) |
| qnfo-idea-triage | 1.3.4-orch-custom-route | 2026-09-06 20:49:21 | qnfo-workers/qnfo-idea-triage | 1.3.4-orch-custom-route | OK |
| qnfo-impact | 0.1.0 | 2026-09-01 09:56:57 | qnfo-workers/qnfo-impact | - | PARTIAL (no repo deployed-current) |
| qnfo-infra | 1.2.3 | 2026-09-05 20:44:04 | qnfo-workers/qnfo-infra | 1.2.3 | OK |
| qnfo-intent-orchestrator | 1.3.4 | 2026-09-05 20:47:40 | qnfo-workers/qnfo-intent-orchestrator | 1.3.4 | OK |
| qnfo-ipatent | 3.4.2 | 2026-09-05 20:47:43 | qnfo-workers/qnfo-ipatent | 3.4.2 | OK |
| qnfo-kaizen | 0.3.0-p2 | 2026-09-04 13:48:43 | qnfo-workers/qnfo-kaizen | 0.3.0-p2 | OK |
| qnfo-lifecycle | 1.6.1-memory-maintain-fixed | 2026-09-01 07:12:40 | qnfo-workers/personal-lifecycle | 1.6.1 | DRIFT repo=1.6.1 |
| qnfo-memory-mcp | 2.0.3 | 2026-09-05 07:15:14 | qnfo-workers/memory-mcp | 2024-11-05 | DRIFT repo=2024-11-05 |
| qnfo-ops | 2.5.1 | 2026-09-06 11:51:07 | qnfo-workers/qnfo-ops | 2.5.1 | OK |
| qnfo-outreach | 0.1.0 | 2026-09-02 22:32:56 | qnfo-workers/qnfo-outreach | 0.1.0 | OK |
| qnfo-paper-indexer | 2.2-scheduled-daily | 2026-08-12 13:07:52 | qnfo-workers/qnfo-paper-indexer | - | PARTIAL (no repo deployed-current) |
| qnfo-paper-reviser | 1.0.2-envelope-safe | 2026-09-06 20:49:21 | qnfo-workers/qnfo-paper-reviser | 1.0.1 | DRIFT repo=1.0.1 |
| qnfo-pdf | 1.0.0 | 2026-09-03 14:35:15 | qnfo-workers/qnfo-pdf | 1.0.0 | OK |
| qnfo-pipeline-ops | 0.5.1-intake-single-issue | 2026-09-06 20:49:21 | qnfo-workers/qnfo-pipeline-ops | 0.5.1-intake-single-issue | OK |
| qnfo-proof | 0.1.0 | 2026-09-04 12:42:42 | qnfo-workers/qnfo-proof | 0.1.0 | OK |
| qnfo-qwav | 2.1.0 | 2026-09-03 13:43:34 | qnfo-workers/qnfo-qwav | - | PARTIAL (no repo deployed-current) |
| qnfo-research-exec | 0.5.16-v2drain-only | 2026-09-06 20:49:21 | qnfo-workers/qnfo-research-exec | 0.5.15-atomic-drain | DRIFT repo=0.5.15-atomic-drain |
| qnfo-research-radar | NO-HEALTH | 2026-09-01 17:45:42 | - | - | GAP (no repo dir) |
| qnfo-research-supervisor | 1.1.1 | 2026-09-06 06:25:13 | qnfo-workers/qnfo-research-supervisor | 1.1.1 | OK |
| qnfo-skill-sync | v1.1.2 | 2026-09-03 13:39:39 | qnfo-workers/qnfo-skill-sync | 1.1.2 | OK |
| qnfo-skills-discovery | 1.1.0 | 2026-09-02 06:15:59 | qnfo-workers/skills-discovery | 1.1.0 | OK |
| qnfo-social | NO-VERSION | 2026-09-04 12:14:53 | qnfo-workers/qnfo-social | UNVERSIONED | PARTIAL (health w/o VERSION) |
| qnfo-system-health | 1.0.2 | 2026-09-06 20:38:41 | qnfo-workers/qnfo-system-health | 1.0.2 | OK |
| qnfo-thread-ingest | 1.0.0 | 2026-08-28 11:59:50 | qnfo-workers/qnfo-thread-ingest | - | PARTIAL (no repo deployed-current) |
| qnfo-tools-mcp | 1.1.2 | 2026-09-04 12:21:54 | qnfo-workers/qnfo-tools-mcp | 1.1.2 | OK |
| qnfo-twin-maintain | NO-HEALTH | 2026-09-01 07:50:03 | - | - | GAP (no repo dir) |
| qnfo-venue-radar | 1.0.3 | 2026-09-03 17:59:03 | qnfo-workers/qnfo-venue-radar | 1.0.3 | OK |
| research-daily-brief | NO-VERSION | 2026-09-02 08:32:20 | - | - | GAP (no repo dir) |

## Consolidation & governance candidates (auto)

Cron-density monoliths (>=4 schedules; merge/split candidates): qnfo-cloud-ops, qnfo-lifecycle, qnfo-social

No canonical repo dir (GAP - re-home per FLEET-SELF-DOC-1 or retire): 13
- job-market-watch, obsidian-writer, osf-integrity-check, personal-life-maintain, qnfo-agent-ws, qnfo-analytics, qnfo-arxiv-radar, qnfo-email, qnfo-gateway, qnfo-idea-miner, qnfo-research-radar, qnfo-twin-maintain, research-daily-brief

Dormant >45d since modified (archive/retire candidates): none

> Advisory output of the recurring integration/consolidation audit (weekly sweep + qnfo-kaizen digest).
> Baseline 2026-09-06: see agent_issues source=qnfo-ops-audit-2026-09-06. Do NOT hand-edit - regenerate.

## Summary

- Total workers: 71
- Self-doc OK: 43
- Drift: 6
- GAP/PARTIAL: 22

## Self-improvement loop

1. Fleet Drift & Self-Improvement Audit cron (weekly): re-runs this sweep, logs drift, repairs via wrangler redeploy.
2. AI Worker Health + Provider Config Guard cron (every 3h): probes qnfo-ai + personal-api chat paths.
3. QNFO Data Freshness Sync cron (every 6h): calendar + email to Vectorize.
4. Kaizen cycles: every lesson becomes a named gate, dual-written. OPS-SELF-DOC.md is the master index.