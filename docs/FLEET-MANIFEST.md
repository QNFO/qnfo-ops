# QNFO FLEET MANIFEST - Cloudflare Workers Ecosystem

> Auto-generated 2026-09-01 21:29 UTC by the fleet self-documentation sweep. Living inventory;
> the weekly Fleet Drift & Self-Improvement Audit cron re-generates it and flags drift.

## Self-documentation policy (FLEET-SELF-DOC-1)

Every worker MUST carry: (1) a VERSION constant reachable via /health; (2) a header comment with purpose, capabilities, deploy method, and Canonical source path; (3) a canonical repo dir under QNFO/qnfo-workers/<name> or QNFO/qnfo-ops/cloud/<name> with a deployed-current.worker.js that byte-matches the deployed bundle. Status: OK = all three; PARTIAL = versioned but not repo-synced; GAP = missing one or more.

## Fleet (48 workers)

| Worker | Live version | Modified (UTC) | Canonical repo | Repo version | Self-doc |
|---|---|---|---|---|---|
| conference-radar | NO-HEALTH | 2026-09-01 11:56:47 | qnfo-workers/conference-radar | UNVERSIONED | PARTIAL (no /health) |
| job-market-watch | NO-HEALTH | 2026-09-01 11:28:57 | - | - | GAP (no repo dir) |
| obsidian-writer | NO-HEALTH | 2026-09-01 11:11:34 | - | - | GAP (no repo dir) |
| osf-integrity-check | NO-HEALTH | 2026-09-01 11:56:24 | - | - | GAP (no repo dir) |
| personal-api | v1.6.1 | 2026-09-01 09:20:10 | - | - | GAP (no repo dir) |
| personal-life-indexer | v2.5-index-auth | 2026-08-20 17:19:11 | - | - | GAP (no repo dir) |
| personal-life-maintain | NO-HEALTH | 2026-09-01 07:27:59 | - | - | GAP (no repo dir) |
| personal-life-search | v1.2.3-env-secret | 2026-08-28 09:48:43 | - | - | GAP (no repo dir) |
| qnfo-agent-orchestrator | v1.0.0 | 2026-09-01 09:55:40 | - | - | GAP (no repo dir) |
| qnfo-agent-ws | 1.3.9 | 2026-08-14 14:50:27 | - | - | GAP (no repo dir) |
| qnfo-ai | 5.11.0 | 2026-09-01 21:18:52 | qnfo-workers/qnfo-ai | 5.11.0 | OK |
| qnfo-ai-patch-test | NO-HEALTH | 2026-09-01 08:44:26 | - | - | GAP (no repo dir) |
| qnfo-ai-search | 1.0.2 | 2026-08-12 06:30:11 | qnfo-workers/qnfo-ai-search | 1.0.2 | OK |
| qnfo-archive | 1.2-cors-fixed | 2026-07-30 12:05:58 | - | - | GAP (no repo dir) |
| qnfo-arxiv-radar | NO-HEALTH | 2026-09-01 18:02:45 | - | - | GAP (no repo dir) |
| qnfo-calibration-audit | NO-HEALTH | 2026-09-01 18:17:33 | - | - | GAP (no repo dir) |
| qnfo-citation-watch | NO-HEALTH | 2026-09-01 17:39:26 | - | - | GAP (no repo dir) |
| qnfo-cloud-ops | 1.6.0 | 2026-09-01 17:41:20 | qnfo-workers/qnfo-cloud-ops | 1.5.0 | DRIFT repo=1.5.0 |
| qnfo-email | NO-HEALTH | 2026-08-31 21:22:10 | - | - | GAP (no repo dir) |
| qnfo-email-orchestrator | 0.3.3 | 2026-09-01 12:06:53 | qnfo-workers/qnfo-email-orchestrator | 0.3.3 | OK |
| qnfo-errata-publish | 0.6.0 | 2026-08-28 16:29:36 | - | - | GAP (no repo dir) |
| qnfo-errata-respond | 0.4.1 | 2026-08-28 17:51:13 | - | - | GAP (no repo dir) |
| qnfo-errata-watch | 0.2.1 | 2026-08-28 17:51:11 | - | - | GAP (no repo dir) |
| qnfo-gateway | 3.4.2-identity-fix-v2 | 2026-08-31 21:22:31 | - | - | GAP (no repo dir) |
| qnfo-idea-factory | 2.4.0 | 2026-09-01 20:35:23 | qnfo-workers/qnfo-idea-factory | UNVERSIONED | DRIFT repo=UNVERSIONED |
| qnfo-idea-triage | 1.1.0 | 2026-09-01 09:54:09 | qnfo-workers/qnfo-idea-triage | 1.1.0 | OK |
| qnfo-impact | 0.1.0 | 2026-09-01 09:56:57 | - | - | GAP (no repo dir) |
| qnfo-indexnow-key | NO-HEALTH | 2026-08-14 06:59:33 | - | - | GAP (no repo dir) |
| qnfo-infra | 1.5.0 | 2026-09-01 21:22:23 | qnfo-workers/qnfo-infra | 1.2.1 | DRIFT repo=1.2.1 |
| qnfo-intent-orchestrator | 1.0.0 | 2026-08-28 09:50:14 | qnfo-workers/qnfo-intent-orchestrator | 1.1.0 | DRIFT repo=1.1.0 |
| qnfo-ipatent | 3.3 | 2026-08-04 17:47:46 | - | - | GAP (no repo dir) |
| qnfo-kaizen | 0.2.0 | 2026-09-01 09:47:33 | - | - | GAP (no repo dir) |
| qnfo-lifecycle | 1.6.1-memory-maintain-fixed | 2026-09-01 07:12:40 | - | - | GAP (no repo dir) |
| qnfo-memory-mcp | 2.0.2 | 2026-08-17 18:16:50 | - | - | GAP (no repo dir) |
| qnfo-ops | 0.4-service-bindings | 2026-08-12 13:49:35 | - | - | GAP (no repo dir) |
| qnfo-outreach | 0.1.0 | 2026-09-01 09:50:24 | - | - | GAP (no repo dir) |
| qnfo-paper-indexer | 2.2-scheduled-daily | 2026-08-12 13:07:52 | - | - | GAP (no repo dir) |
| qnfo-qwav | 2.1.0 | 2026-08-28 12:24:11 | - | - | GAP (no repo dir) |
| qnfo-research-radar | NO-HEALTH | 2026-09-01 17:45:42 | - | - | GAP (no repo dir) |
| qnfo-secrets-audit | NO-HEALTH | 2026-09-01 18:14:38 | - | - | GAP (no repo dir) |
| qnfo-skill-sync | v1.1.2 | 2026-08-21 08:18:46 | - | - | GAP (no repo dir) |
| qnfo-skills-discovery | NO-HEALTH | 2026-08-11 15:12:02 | - | - | GAP (no repo dir) |
| qnfo-social | True | 2026-08-31 21:22:13 | qnfo-workers/qnfo-social | UNVERSIONED | DRIFT repo=UNVERSIONED |
| qnfo-system-health | NO-HEALTH | 2026-09-01 17:48:38 | - | - | GAP (no repo dir) |
| qnfo-thread-ingest | 1.0.0 | 2026-08-28 11:59:50 | - | - | GAP (no repo dir) |
| qnfo-tools-mcp | 1.1.0 | 2026-08-28 11:06:31 | qnfo-workers/qnfo-tools-mcp | 1.1.0 | OK |
| qnfo-twin-maintain | NO-HEALTH | 2026-09-01 07:50:03 | - | - | GAP (no repo dir) |
| research-daily-brief | True | 2026-09-01 09:27:32 | - | - | GAP (no repo dir) |

## Summary

- Total workers: 48
- Self-doc OK: 5
- Drift/partial/gap: 43
- NO-HEALTH rows are expected for cron-only utility workers (no HTTP surface).

## Self-improvement loop

1. Fleet Drift & Self-Improvement Audit cron (weekly): re-runs this sweep, logs drift to qnfo-audit D1, repairs where the fix is a documented one-liner (wrangler deploy from canonical repo).
2. AI Worker Health + Provider Config Guard cron (every 3h): probes qnfo-ai + personal-api chat paths and DeepChat provider config.
3. QNFO Data Freshness Sync cron (every 6h): keeps Vectorize fresh with calendar + email.
4. Kaizen cycles (CMD SKILLS UPDATE): every session lesson becomes a named gate in skills + system prompt (dual-written, parity-verified).