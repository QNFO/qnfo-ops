# QNFO FLEET MANIFEST — Cloudflare Workers Ecosystem

> Auto-generated 2026-09-02 06:17 UTC by the fleet self-documentation sweep.
> Cycle-1 refresh 2026-09-02 ~19:20 UTC (QNFO.OPS.011): qnfo-ai 5.16.3, qnfo-intent-orchestrator 1.3.2,
> qnfo-blank-audit 1.1.0, + qnfo-chat-canary 1.0.1 (behavioral chat canary + sent-guard).
> Cycle-2 refresh 2026-09-02 ~20:45 UTC (QNFO.OPS.AUDITLOOP.001): + qnfo-auditor 1.0.0 (fleet event audit & act loop).
> Cycle-3 refresh 2026-09-02 ~21:50 UTC (ERRATA-WORKFLOW-MIGRATION): + qnfo-errata-orchestrator 1.0.0 (ErrataWorkflow durable orchestration);
> Cycle-4 refresh 2026-09-03 ~06:25 UTC (OPS-AI-ENDPOINT): qnfo-ops v0.4 stub -> v1.0.1 ops AI execution endpoint (repo qnfo-workers/qnfo-ops); qnfo-ai 5.16.6 auto-express guard keeps ops commands out of the ideas/research stream.
> Cycle-5 refresh 2026-09-03 ~08:00 UTC (OPS-ENDPOINT-FULL-INTEGRATION): qnfo-ops 1.0.3 (d1 read-only guard hardened - mutation keywords blocked anywhere; daily cap 250/UTC day; /v1/models capability advertisement chat/agent/code/streaming/tool_use); qnfo-ai 5.16.7 (guard covers worker-name health/status phrasing; /v1/models capabilities advertised); ops endpoint registered in DeepChat (provider QNFO-OPS + agent ops) and ChatBox Windows (provider qnfo-ops); ChatBox qnfo-router roster synced to live 22 models.
> Cycle-6 refresh 2026-09-03 ~09:00 UTC (WHAT-ELSE EXEC): qnfo-ops 1.0.4 (/cost route; guarded email_mark/email_respond reply-to-inbound w/ negation-aware user affirmation + spam-token subject rejection); qnfo-chat-canary 1.0.2 (ops-feed guard probe - ops phrase w/ chat UA must not auto-express; once/day + cleanup + HIGH alert); qnfo-cloud-ops 1.12.0 (visibility digest adds ops AI 7d section: chats/cost/tool events/drains).
> legacy errata watch/respond/publish now step-executors behind errata-workflow (crons disabled 2026-09-02).
> Living inventory; weekly Fleet Drift cron (42b1988c) re-generates and flags drift.

## Self-documentation policy (FLEET-SELF-DOC-1)

Every worker MUST carry: (1) VERSION reachable via /health; (2) header with purpose/canonical source; (3) canonical repo deployed-current.worker.js. Status: OK = all; PARTIAL = versioned not repo-synced; GAP = missing one or more.

## Fleet (56 workers)

| Worker | Live version | Modified (UTC) | Canonical repo | Repo version | Self-doc |
|---|---|---|---|---|---|
| qnfo-backlog-exec | 1.1.1 | 2026-09-02 18:31 UTC | qnfo-workers/qnfo-backlog-exec | 1.1.1 | OK |
| events-radar | 1.0.0 | 2026-09-02 10:51:19 | qnfo-workers/events-radar | 1.0.0 | OK |
| calendar-api | 0.3.0 | 2026-09-03 06:47:00 | qnfo-workers/calendar | 0.3.0 | OK |
| personal-events-radar | 1.2.3 | 2026-09-02 16:10:00 | qnfo-workers/personal-events-radar | 1.2.3 | OK |
| job-market-watch | NO-HEALTH | 2026-09-01 11:28:57 | - | - | GAP (no repo dir) |
| obsidian-writer | NO-HEALTH | 2026-09-01 11:11:34 | - | - | GAP (no repo dir) |
| osf-integrity-check | NO-HEALTH | 2026-09-01 11:56:24 | - | - | GAP (no repo dir) |
| personal-api | v3.0.4 | 2026-09-03 06:58:00 | qnfo-workers/personal-api | v3.0.4 | OK |
| personal-life-indexer | v2.5-index-auth | 2026-08-20 17:19:11 | - | - | GAP (no repo dir) |
| personal-life-maintain | NO-HEALTH | 2026-09-01 07:27:59 | - | - | GAP (no repo dir) |
| personal-life-search | v1.2.3-env-secret | 2026-08-28 09:48:43 | - | - | GAP (no repo dir) |
| qnfo-agent-orchestrator | v1.0.0 | 2026-09-01 09:55:40 | - | - | GAP (no repo dir) |
| qnfo-agent-ws | 1.3.9 | 2026-08-14 14:50:27 | - | - | GAP (no repo dir) |
| qnfo-ai | 5.16.9 | 2026-09-03 08:10 UTC | qnfo-workers/qnfo-ai | 5.16.9 | OK |
| qnfo-ai-patch-test | NO-HEALTH | 2026-09-01 08:44:26 | - | - | GAP (no repo dir) |
| qnfo-ai-search | 1.0.2 | 2026-08-12 06:30:11 | qnfo-workers/qnfo-ai-search | 1.0.2 | OK |
| qnfo-archive | 1.2-cors-fixed | 2026-07-30 12:05:58 | - | - | GAP (no repo dir) |
| qnfo-arxiv-radar | NO-HEALTH | 2026-09-01 18:02:45 | - | - | GAP (no repo dir) |
| qnfo-blank-audit | 1.1.0 | 2026-09-02 19:03:00 | qnfo-workers/qnfo-blank-audit | 1.1.0 | OK |
| qnfo-chat-canary | 1.0.2 | 2026-09-03 08:55 UTC | qnfo-workers/qnfo-chat-canary | 1.0.2 | OK |
| qnfo-calibration-audit | NO-HEALTH | 2026-09-01 18:17:33 | - | - | GAP (no repo dir) |
| qnfo-citation-watch | 1.0.0 | 2026-09-03 06:20 UTC | qnfo-workers/qnfo-citation-watch | 1.0.0 | OK (workers.dev route re-enabled 2026-09-03; canonical dir created) |
| qnfo-cloud-ops | 1.13.0 | 2026-09-03 06:30 UTC | qnfo-workers/qnfo-cloud-ops | 1.13.0 | OK (OUTREACH-ENGINE-LIVE-1 gate + email validation) |
| qnfo-events | 1.0.2 | 2026-09-02 19:57 UTC | qnfo-workers/qnfo-events | 1.0.2 | OK |
| qnfo-auditor | 1.1.2 | 2026-09-02 21:08 UTC | qnfo-workers/qnfo-auditor | 1.1.2 | OK |
| qnfo-email | NO-HEALTH | 2026-08-31 21:22:10 | - | - | GAP (no repo dir) |
| qnfo-email-orchestrator | 0.3.3 | 2026-09-01 12:06:53 | qnfo-workers/qnfo-email-orchestrator | 0.3.3 | OK |
| qnfo-errata-orchestrator | 1.0.0 | 2026-09-02 21:47 UTC | qnfo-workers/errata-orchestrator | 1.0.0 | OK |
| qnfo-errata-publish | 0.6.0 | 2026-08-28 | qnfo-workers/qnfo-errata-publish | 0.6.0 | OK |
| qnfo-errata-respond | 0.4.1 | 2026-08-28 | qnfo-workers/qnfo-errata-respond | 0.4.1 | OK |
| qnfo-errata-watch | 0.2.1 | 2026-08-28 | qnfo-workers/qnfo-errata-watch | 0.2.1 | OK |
| qnfo-gateway | 3.4.2-identity-fix-v2 | 2026-08-31 21:22:31 | - | - | GAP (no repo dir) |
| qnfo-idea-factory | 2.4.0 | 2026-09-01 20:35:23 | qnfo-workers/qnfo-idea-factory | UNVERSIONED | DRIFT repo=UNVERSIONED |
| qnfo-idea-triage | 1.1.0 | 2026-09-01 09:54:09 | qnfo-workers/qnfo-idea-triage | 1.1.0 | OK |
| qnfo-impact | 0.1.0 | 2026-09-01 09:56:57 | - | - | GAP (no repo dir) |
| qnfo-indexnow-key | NO-HEALTH | 2026-08-14 06:59:33 | - | - | GAP (no repo dir) |
| qnfo-infra | 1.5.0 | 2026-09-01 21:22:23 | qnfo-workers/qnfo-infra | 1.2.1 | DRIFT repo=1.2.1 |
| qnfo-intent-orchestrator | 1.3.2 | 2026-09-02 19:14:00 | qnfo-workers/qnfo-intent-orchestrator | 1.3.2 | OK |
| qnfo-ipatent | 3.3 | 2026-08-04 17:47:46 | - | - | GAP (no repo dir) |
| qnfo-kaizen | 0.2.0 | 2026-09-01 09:47:33 | - | - | GAP (no repo dir) |
| qnfo-lifecycle | 1.6.1-memory-maintain-fixed | 2026-09-01 07:12:40 | - | - | GAP (no repo dir) |
| qnfo-memory-mcp | 2.0.2 | 2026-08-17 18:16:50 | - | - | GAP (no repo dir) |
| qnfo-ops | 1.0.4 | 2026-09-03 08:55 UTC | qnfo-workers/qnfo-ops | 1.0.4 | OK |
| qnfo-outreach | 0.1.0 | 2026-09-03 | qnfo-workers/qnfo-outreach | 0.1.0 | OK (campaign pipeline; ACTIVATION_AT 2026-09-15) |
| qnfo-paper-indexer | 2.2-scheduled-daily | 2026-08-12 13:07:52 | - | - | GAP (no repo dir) |
| qnfo-pdf | NO-HEALTH | 2026-09-02 18:34 | - | - | GAP (no repo dir) |
| qnfo-qwav | 2.1.0 | 2026-08-28 12:24:11 | - | - | GAP (no repo dir) |
| qnfo-research-radar | NO-HEALTH | 2026-09-01 17:45:42 | - | - | GAP (no repo dir) |
| qnfo-secrets-audit | NO-HEALTH | 2026-09-01 18:14:38 | - | - | GAP (no repo dir) |
| qnfo-skill-sync | v1.1.2 | 2026-08-21 08:18:46 | - | - | GAP (no repo dir) |
| qnfo-skills-discovery | 1.1.0 | 2026-09-02 06:15:59 | - | - | GAP (no repo dir) |
| qnfo-social | NO-HEALTH | 2026-08-31 21:22:13 | qnfo-workers/qnfo-social | UNVERSIONED | GAP (no /health) |
| qnfo-system-health | NO-HEALTH | 2026-09-01 17:48:38 | - | - | GAP (no repo dir) |
| qnfo-thread-ingest | 1.0.0 | 2026-08-28 11:59:50 | - | - | GAP (no repo dir) |
| qnfo-tools-mcp | 1.1.0 | 2026-08-28 11:06:31 | qnfo-workers/qnfo-tools-mcp | 1.1.0 | OK |
| qnfo-twin-maintain | NO-HEALTH | 2026-09-01 07:50:03 | - | - | GAP (no repo dir) |
| research-daily-brief | NO-HEALTH | 2026-09-01 09:27:32 | - | - | GAP (no repo dir) |

## Summary

- Total workers: 54
- Self-doc OK: 11
- Drift: 4
- GAP/PARTIAL: 39

## Self-improvement loop

1. Fleet Drift & Self-Improvement Audit cron (weekly): re-runs sweep, logs drift, repairs via wrangler redeploy.
2. AI Worker Health + Provider Config Guard cron (every 3h): probes qnfo-ai + personal-api chat paths.
3. QNFO Data Freshness Sync cron (every 6h): calendar + email to Vectorize.
4. Kaizen cycles: every lesson becomes a named gate, dual-written. OPS-SELF-DOC.md is the master index.