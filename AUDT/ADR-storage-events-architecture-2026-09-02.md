# ADR: QNFO storage & events architecture (2026-09-02)

Status: ACCEPTED (agent decision; user delegated all choices 2026-09-02)
Owner: qnfo-cloud-ops fleet / autonomous pipeline

## Context
Alert email was the primary issue-tracking channel, inefficient for repeats.
Session built qnfo-events (D1 issue ledger). User: CF already has native
events/messaging; D1 may not suit all data; what D1 data should move?

## Decision
1. Raw append-only telemetry (errors/warnings/info, event streams) ->
   Workers Analytics Engine (writeDataPoint, SQL) + R2 cold archive (Logpush).
2. Messaging / fan-out -> Cloudflare Queues (retries + DLQ). Email only for a
   daily unresolved-HIGH digest.
3. Curated mutable state needing ACID + joins + lifecycle -> D1 stays home:
   issue_ledger (qnfo-events), scheduler_state, outreach/errata/tasks, KG.
4. Blobs (email bodies, chat transcripts, living-paper body_md ~39MB,
   personal-life ~23MB) -> R2 objects (+ R2 SQL) with slim D1 indexes.
5. Semantic search stays on Vectorize.
## Consequences
- qnfo-events v1.0.2 stays as the small D1 issue tracker (right-sized).
- New qnfo-telemetry worker = Analytics Engine ingestion endpoint.
- Queues worker + R2 blob migrations tracked as agent_issues.

## Evidence
CF docs 2026-09-02 (Queues JS APIs; Analytics Engine SQL 2025-09/11; Pipelines;
Logpush workers logs; R2 SQL). D1 inventory: qnfo-audit ~25MB, living-paper
~39MB, personal-life ~23MB, qnfo-graph ~8MB, portfolio-state/ipatent/outreach/cms.
