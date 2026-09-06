# QNFO Fleet SLA — Service-Level Agreement (systemwide/fleetwide)

Canonical: QNFO/qnfo-ops/docs/SLA.md (2026-09-06, user directive: no multi-week waits; accelerate all rows).

## Hard rule
No open task_dod_register row may carry a due date more than 7 days out unless it is
calendar-bound (a named future date event, e.g. RESTORE-DRILL, Q3 rebalance) OR volume-bound
(a drain whose size, not latency, sets the horizon — e.g. 329-record Zenodo versioning).
Every other row resolves within its tier below.

## Resolution tiers (level-of-service)
| Tier | Class | Max resolve | Mechanism (user-free) |
|------|-------|-------------|-----------------------|
| S0 critical | prod-down / security / data-loss | 24h | durable job + out-of-band alert |
| S1 high | broken core feature / stalled pipeline | 72h | durable job / cloud cron |
| S2 medium | degraded / non-blocking bug / quality outlier | 5d | cloud cron + kaizen |
| S3 low | enhancement / housekeeping / backlog drain | 7d | cloud cron / scheduled-runner |

## Enforcement
- Row 95 (kaizen 09-07) is the enforcement sweep: every agent-owned row must carry a dated
  cloud trigger or durable executor; anything past its tier max is escalated, not silently deferred.
- v_waiting_on_human MUST stay 0: rows resolve autonomously (execute / dated scheduled-runner /
  cancel-with-rationale), never owner=user waiting.
