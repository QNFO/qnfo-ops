# QNFO FLEET MANIFEST — Cloudflare Workers Ecosystem

> Auto-generated 2026-09-04 12:53 UTC by fleet-manifest-sweep.py v2.0 (self-contained enumeration + /health probes).
> Living inventory; weekly Fleet Drift cron (42b1988c) re-generates this file from live CF state - do NOT hand-edit;
> deploy history lives in qnfo-audit deployment_history + git log.

## Self-documentation policy (FLEET-SELF-DOC-1)

Every worker MUST carry: (1) VERSION reachable via /health; (2) header with purpose/canonical source;
(3) canonical repo deployed-current.worker.js. Status: OK = all; PARTIAL = versioned not repo-synced;
GAP = missing one or more. AUTH-GATED = /health behind auth (monitor must send bearer).

## Fleet (65 workers)

| Worker | Live version | Modified (UTC) | Canonical repo | Repo version | Self-doc |
|---|---|---|---|---|---|
| calendar-api | 0.3.0 | 2026-09-03 04:46:55 | qnfo-workers/calendar | 0.3.0 | OK |
| events-radar | 1.0.1 | 2026-09-02 11:14:48 | qnfo-workers/events-radar | 1.0.1 | OK |
| job-market-watch | NO-HEALTH | 2026-09-01 11:28:57 | - | - | GAP (no repo dir) |
| obsidian-writer | NO-HEALTH | 2026-09-01 11:11:34 | - | - | GAP (no repo dir) |
| osf-integrity-check | NO-VERSION | 2026-09-01 11:56:24 | - | - | GAP (no repo dir) |
| personal-api | v3.1.0-p1 | 2026-09-03 13:39:49 | qnfo-workers/personal-api | v3.1.0 | DRIFT repo=v3.1.0 |
| personal-events-radar | 1.2.4 | 2026-09-03 04:46:37 | qnfo-workers/personal-events-radar | 1.2.4 | OK |
| personal-life-indexer | v2.5-index-auth | 2026-08-20 17:19:11 | - | - | GAP (no repo dir) |
| personal-life-maintain | NO-HEALTH | 2026-09-01 07:27:59 | - | - | GAP (no repo dir) |
| personal-life-search | v1.2.3-env-secret | 2026-08-28 09:48:43 | - | - | GAP (no repo dir) |
| qnfo-agent-orchestrator | v1.0.0 | 2026-09-03 13:38:01 | qnfo-workers/agent-orchestrator | 1.0.0 | OK |
| qnfo-agent-ws | 1.3.9 | 2026-08-14 14:50:27 | - | - | GAP (no repo dir) |
| qnfo-ai | 5.20.12 | 2026-09-04 05:07:02 | qnfo-workers/qnfo-ai | 5.20.12 | OK |
| qnfo-ai-calibration | 1.0.2 | 2026-09-04 03:39:35 | qnfo-workers/qnfo-ai-calibration | 1.0.2 | OK |
| qnfo-ai-patch-test | NO-HEALTH | 2026-09-02 08:35:26 | - | - | GAP (no repo dir) |
| qnfo-ai-search | 1.0.2 | 2026-08-12 06:30:11 | qnfo-workers/qnfo-ai-search | 1.0.2 | OK |
| qnfo-archive | 1.2-cors-fixed | 2026-07-30 12:05:58 | - | - | GAP (no repo dir) |
| qnfo-arxiv-radar | NO-HEALTH | 2026-09-01 18:02:45 | - | - | GAP (no repo dir) |
| qnfo-auditor | 1.1.7 | 2026-09-04 02:07:58 | qnfo-workers/qnfo-auditor | 1.1.7 | OK |
| qnfo-backlog-exec | 1.1.1 | 2026-09-02 18:31:50 | qnfo-workers/qnfo-backlog-exec | 1.1.1 | OK |
| qnfo-blank-audit | 1.1.0 | 2026-09-02 20:34:47 | qnfo-workers/qnfo-blank-audit | 1.1.0 | OK |
| qnfo-chat-canary | 1.0.2 | 2026-09-03 04:57:33 | qnfo-workers/qnfo-chat-canary | 1.0.2 | OK |
| qnfo-citation-watch | 1.0.0 | 2026-09-03 05:51:42 | qnfo-workers/qnfo-citation-watch | 1.0.0 | OK |
| qnfo-cloud-ops | 1.13.1 | 2026-09-04 02:14:09 | qnfo-workers/qnfo-cloud-ops | 1.13.1 | OK |
| qnfo-ddocs-indexer | v1.0-server-side | 2026-09-04 09:55:53 | qnfo-workers/qnfo-ddocs-indexer | UNVERSIONED | DRIFT repo=UNVERSIONED |
| qnfo-email | AUTH-GATED | 2026-08-31 21:22:10 | - | - | GAP (no repo dir) |
| qnfo-email-orchestrator | 0.3.3-p1-p1 | 2026-09-03 13:38:46 | qnfo-workers/qnfo-email-orchestrator | 0.3.3 | DRIFT repo=0.3.3 |
| qnfo-errata-orchestrator | 1.0.0 | 2026-09-02 21:47:31 | qnfo-workers/errata-orchestrator | 1.0.0 | OK |
| qnfo-errata-publish | 0.7.0 | 2026-09-04 01:59:16 | qnfo-workers/qnfo-errata-publish | 0.7.0 | OK |
| qnfo-errata-respond | 0.4.1 | 2026-09-03 13:38:10 | qnfo-workers/qnfo-errata-respond | 0.4.1 | OK |
| qnfo-errata-watch | 0.2.1 | 2026-09-03 13:38:14 | qnfo-workers/qnfo-errata-watch | 0.2.1 | OK |
| qnfo-events | 1.1.0 | 2026-09-04 02:04:15 | qnfo-workers/qnfo-events | 1.1.0 | OK |
| qnfo-fleet-calibrator | 1.0.0 | 2026-09-04 05:10:58 | qnfo-workers/qnfo-fleet-calibrator | 1.0.0 | OK |
| qnfo-gateway | NO-HEALTH | 2026-09-03 18:23:45 | - | - | GAP (no repo dir) |
| qnfo-idea-factory | 2.7.2 | 2026-09-03 05:42:35 | qnfo-workers/qnfo-idea-factory | 2.7.2 | OK |
| qnfo-idea-miner | NO-HEALTH | 2026-09-03 13:37:06 | - | - | GAP (no repo dir) |
| qnfo-idea-triage | 1.1.0-p1 | 2026-09-03 13:37:50 | qnfo-workers/qnfo-idea-triage | 1.1.0 | DRIFT repo=1.1.0 |
| qnfo-impact | 0.1.0 | 2026-09-01 09:56:57 | - | - | GAP (no repo dir) |
| qnfo-indexnow-key | NO-HEALTH | 2026-08-14 06:59:33 | - | - | GAP (no repo dir) |
| qnfo-infra | 1.5.1 | 2026-09-02 18:07:09 | qnfo-workers/qnfo-infra | 1.2.1 | DRIFT repo=1.2.1 |
| qnfo-intent-orchestrator | 1.3.4 | 2026-09-04 01:42:37 | qnfo-workers/qnfo-intent-orchestrator | 1.3.4 | OK |
| qnfo-ipatent | 3.4.2 | 2026-09-03 13:38:56 | qnfo-workers/qnfo-ipatent | 3.4.2 | OK |
| qnfo-kaizen | 0.3.0-p1 | 2026-09-04 11:59:51 | qnfo-workers/qnfo-kaizen | 0.3.0-p1 | OK |
| qnfo-latex | NO-HEALTH | 2026-09-03 14:52:32 | - | - | GAP (no repo dir) |
| qnfo-lifecycle | 1.6.1-memory-maintain-fixed | 2026-09-01 07:12:40 | qnfo-workers/personal-lifecycle | 1.0.0 | DRIFT repo=1.0.0 |
| qnfo-memory-mcp | 2.0.2 | 2026-08-17 18:16:50 | qnfo-workers/memory-mcp | 2024-11-05 | DRIFT repo=2024-11-05 |
| qnfo-ops | 1.8.0 | 2026-09-04 11:52:06 | qnfo-workers/qnfo-ops | 1.8.0 | OK |
| qnfo-outreach | 0.1.0 | 2026-09-02 22:32:56 | qnfo-workers/qnfo-outreach | 0.1.0 | OK |
| qnfo-paper-indexer | 2.2-scheduled-daily | 2026-08-12 13:07:52 | - | - | GAP (no repo dir) |
| qnfo-pdf | 1.0.0 | 2026-09-03 14:35:15 | qnfo-workers/qnfo-pdf | 1.0.0 | OK |
| qnfo-pipeline-ops | NO-HEALTH | 2026-09-04 12:19:56 | - | - | GAP (no repo dir) |
| qnfo-proof | 0.1.0 | 2026-09-04 12:42:42 | qnfo-workers/qnfo-proof | 0.1.0 | OK |
| qnfo-qwav | 2.1.0 | 2026-09-03 13:43:34 | - | - | GAP (no repo dir) |
| qnfo-research-exec | 0.5.9-note-fallback | 2026-09-04 12:40:59 | qnfo-workers/qnfo-research-exec | 0.4.9-p1 | DRIFT repo=0.4.9-p1 |
| qnfo-research-radar | NO-HEALTH | 2026-09-01 17:45:42 | - | - | GAP (no repo dir) |
| qnfo-secrets-audit | NO-HEALTH | 2026-09-01 18:14:38 | - | - | GAP (no repo dir) |
| qnfo-skill-sync | v1.1.2 | 2026-09-03 13:39:39 | qnfo-workers/qnfo-skill-sync | 1.1.2 | OK |
| qnfo-skills-discovery | 1.1.0 | 2026-09-02 06:15:59 | qnfo-workers/skills-discovery | 1.1.0 | OK |
| qnfo-social | NO-VERSION | 2026-09-04 12:14:53 | qnfo-workers/qnfo-social | UNVERSIONED | PARTIAL (health w/o VERSION) |
| qnfo-system-health | NO-HEALTH | 2026-09-01 17:48:38 | - | - | GAP (no repo dir) |
| qnfo-thread-ingest | 1.0.0 | 2026-08-28 11:59:50 | - | - | GAP (no repo dir) |
| qnfo-tools-mcp | 1.1.2 | 2026-09-04 12:21:54 | qnfo-workers/qnfo-tools-mcp | 1.1.2 | OK |
| qnfo-twin-maintain | NO-HEALTH | 2026-09-01 07:50:03 | - | - | GAP (no repo dir) |
| qnfo-venue-radar | 1.0.3 | 2026-09-03 17:59:03 | qnfo-workers/qnfo-venue-radar | 1.0.3 | OK |
| research-daily-brief | NO-VERSION | 2026-09-02 08:32:20 | - | - | GAP (no repo dir) |

## Summary

- Total workers: 65
- Self-doc OK: 31
- Drift: 8
- GAP/PARTIAL: 26

## Self-improvement loop

1. Fleet Drift & Self-Improvement Audit cron (weekly): re-runs this sweep, logs drift, repairs via wrangler redeploy.
2. AI Worker Health + Provider Config Guard cron (every 3h): probes qnfo-ai + personal-api chat paths.
3. QNFO Data Freshness Sync cron (every 6h): calendar + email to Vectorize.
4. Kaizen cycles: every lesson becomes a named gate, dual-written. OPS-SELF-DOC.md is the master index.