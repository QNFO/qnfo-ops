# QNFO/QWAV Full-Stack Integration Defects — 2026-09-13

Companion to `SELF-AUDIT-GAPS-2026-09-03.md`. Author: qnfo-ops / ops-exec.
Every figure is a live tool return from the 2026-09-13 session. Ops-workspace mirror:
`ops-workspace/audits/2026-09-13-quniverse-architecture-and-integration-audit.md`.

> **CORRECTION 2.** Revision 1 asserted "the self-governing layer does not exist." **Wrong,
> withdrawn** — see §3.2. `governance_kernel` is `ACTIVE` with 13 ratified gates and is
> actively blocking writes. The defect is fragmentation and infrequent exercise, not absence.
>
> **CORRECTION 3 (this revision).** D12's weekly-cron finding was published as "a signal, not
> proof" on one source. It is now **corroborated by three further independent tables** — and
> the corroboration exposed **D16: the SAI/report-card time series is effectively empty**
> (1 row, `sai` and `grade` both NULL).

## 0. Term caveat

"Quniverse" appears in no store reachable from the ops endpoint (Vectorize research/notes/tasks/
handoffs = 0 literal matches; D1 living/graph/audit = no row, node, table or issue). Nearest real
entities: **QWAV** (legacy research platform, worker `qnfo-qwav`) and the **QNFO** fleet. This
document describes the QNFO/QWAV system as a whole.

## 1. Mission and architecture (canonical pointers)

- **Fleet** — `docs/AUTONOMOUS-FLEET-ARCHITECTURE.md` (AF-1 v1.0, 2026-09-10, PROPOSED):
  every recurring function runs in the cloud; the fleet operates, heals, audits, improves,
  publishes and promotes itself; the human narrows to policy-setting and exception handling.
  Success metric = **Watchmaker Index** → ~0. Layers L0–L7; axioms A1–A10; Worker Contract v1;
  autonomy ladder L0–L3; ALVE-1 metrics.
- **Research** — `docs/SIGNAL-ORGANISM-ARCHITECTURE.md` (v1.0, 2026-09-12, ACTIVE):
  signal-constituted research organism; every artifact responds to a detected signal; every
  signal audited for what it does not establish; refinement unsupervised; every output deposited
  as a citable, attributable natural-language object; **JPCUB** as the fitness function.
  Layers L0–L8, where **L8 (artifact → signal re-entry)** closes the loop.

AF-1 is the substrate (operations); the signal-organism is the payload (research).

## 2. Defects (ranked)

### D14 — SPLIT-BRAIN ISSUE LEDGERS (25× under-report) — highest severity

| Store | Open | Visible to ops tooling? |
|---|---|---|
| `agent_issues` | **12** | Yes (`backlog_status`, `ops_issues_list`) |
| `issue_ledger` | **305** | **No** |
| `fleet_issue_log` | 41 rows | No |
| `fleet_issue_dispatch` | 34 rows | No |

`issue_ledger` grew **270 → 305 open between ~06:45Z and 12:21Z on 2026-09-13** (+35 in ~5.5h
≈ 150/day). Axiom A3 violated at the governance layer: the instrument that measures the backlog
is not connected to the backlog. Ops reports sourced from `agent_issues` under-state open work
by ~25×.

### D16 — The SAI / report-card time series is effectively empty (NEW)

The fleet's headline health metric has no usable history:

- `report_card_history`: **1 row total** — `id=1`, `ts=2026-09-10T12:33:04Z`,
  **`sai = NULL`, `grade = NULL`**. Its `signals_json` reads
  `{"source":"cloud-weekly-cron-trigger","user_wait":0,"open_issues":4,"unversioned":6}` —
  i.e. the row is a *trigger record*, not a scored result.
- `benchmark_results`: **6 rows, all within 4 seconds** (`2026-09-10T12:30:26Z` →
  `12:30:30Z`). The entire benchmark history is a single battery run.
- Root cause is visible in the run ledger: `fleet_runs` id=111, `report-card-weekly`,
  **failed 2026-09-10T12:32:58Z**, `D1_ERROR: table report_card_history has no column named
  source`. The write that would populate the series fails on a schema mismatch — which is why
  the trigger value `"source"` is stuffed into `signals_json` instead of its own column.
- Meanwhile SAI values survive only as **free text inside event rows** (`cloud_ops_events`:
  68.0 → 68.3 → 68.7 on 2026-09-10), not as structured series data.

Consequence: SAI is a headline ALVE-1 metric with **no queryable trend**, so no metric built on
it (integration factor, report card, weekly watchtower) can be time-series validated.

### D15 — 209 tables in `qnfo-audit`; parallel ledgers by accretion

`SELECT COUNT(*) FROM sqlite_master WHERE type='table'` = **209**:

- **issues (6)**: `agent_issues`, `issue_ledger`, `issue_events`, `fleet_issue_log`,
  `fleet_issue_dispatch`, `fleet_issue_loop`
- **tasks (8)**: `tasks`, `tasks_wbs`, `task_dod_register`, `subtasks`, `phases`,
  `pipeline_tasks`, `fleet_tasks`, `gtd_register`
- **projects (6)**: `projects`, `project_ledger`, `project_state`, `portfolios`, `programs`,
  `stale_projects`
- **analytics (12)**: `analytics_dash_*` ×8 + `analytics_ae_events`, `analytics_daily`,
  `analytics_events`, `analytics_metric_triggers`
- **calibration (10)**: `fleet_cal_*` ×7 + `ai_calibration_*` ×3
- **governance / self-modification (8+)**: `governance_kernel`, `gov_gate_log`,
  `autonomy_scores`, `self_rewrite_state` (67), `evolve_candidates`, `evolve_rollback` (41),
  `freshness_guard` (16), `decisions`, `adr*`, `meta_claims`, `meta_changes`
- **duplicated-and-abandoned**: `r2_files` (0 rows) + `r2_files_new` (0 rows);
  `cf_pages_domain_mappings` + `cf_pages_domain_mappings_new`

No declared owner per domain. This is the structural cause of integration difficulty, not a
single drift.

### D1 — Liveness sensing covers 14.5% of the fleet

Live probe set = **10 targets** (8 workers + 2 sites): `qnfo-social`, `qnfo-paper-reviser`,
`qnfo-outreach`, `qnfo-ops`, `qnfo-kaizen`, `qnfo-fleet-dashboard`, `qnfo-ai`, `personal-api`,
`qnfo.org`, `papers.qnfo.org`. Deployed workers = **55** → **47 workers with zero liveness
verification**. AF-1 Tier-3 floor states "universal… target 100%". Note `autonomy_scores`
(scored 2026-09-10) cites "81/81 probes" — **stale** against live coverage.

### D12 — Scheduling observability is thin, and the weekly Monday fires did not happen

- **Run ledger** `fleet_runs`: **20 distinct cron names, 482 runs, earliest 2026-09-10T07:00Z**
  against **40 scheduled workers**. Since 09-11 only three crons appear.
- **Cron registry** `fleet_crons`: **6 rows, 5 enabled** against the same 40.

**Weekly-fire finding, now corroborated by four sources.** 2026-09-07 was a **Monday**; the two
weekly Monday crons (`report-card-weekly-cron` `30 6 * * 1`, `bench-arc-weekly` `0 8 * * 1`)
show no execution on that date anywhere:

| source | report-card | bench-arc | 2026-09-07? |
|---|---|---|---|
| `fleet_crons.last_fired` | Thu 09-10 12:32Z | Thu 09-10 12:29Z | absent |
| `cloud_ops_events` (kind) | 3 rows, all 09-10 | 2 rows, all 09-10 | absent |
| `report_card_history` | 1 row, 09-10 | — | absent |
| `benchmark_results` | — | 6 rows, all 09-10 12:30 | absent |

**Caveat that limits the claim:** every record clusters inside `2026-09-10T12:18–12:33Z`, which
looks like a single bootstrap/expansion session rather than routine scheduled firing. So the
honest statement is: **there is no evidence these weekly crons have ever fired on schedule**,
and the 09-10 cluster is one manual/cloud-triggered bootstrap. `last_fired` may be seeded.

### D13 — `venue-radar-scan`: 100% failed, daily, unhealed, unescalated

3 runs / 3 failures, `unsupported step type: venue`, on 09-11, 09-12 and 09-13. Absent from the
open `agent_issues` set and not repaired by the self-heal loop.

### D4 — Self-heal loop failing hourly with no backoff or circuit breaker

`fleet_deploys` since 2026-09-11:

| worker | ok=0 | window |
|---|---|---|
| `personal-companion` | **26** | 09-12 09:01Z → 09-13 **13:01Z (still firing)** |
| `qnfo-cloud-ops` | **25** | 09-12 10:01Z → 09-13 07:02Z |

`personal-companion` attempts `v1.1.0 → 1.0.0`: the healer repeatedly attempts a **downgrade** to
the registry version. `self_heal_actions` (1,372 rows): healed 528, **deferred 445**,
**detected 170**, resolved 130, **failed 50**, dispatched 35, executed 10 → **615 findings
counted but not closed**, violating AF-1 `DRIFT-SELFHEAL-WIRING-1`.

### D7 (REWRITTEN) — The governing layer exists but is fragmented and barely exercised

`governance_kernel`: **1 row**, `kernel_version = 2026-09-01.1`, `status = ACTIVE`,
`ratified_on = 2026-09-01 08:39:03`, `spec_ref = docs/THIN-CLIENT-MIGRATION-SPEC-V2.md §4`,
`autonomy_boundary` = "procedural/process/optimization content BELOW the kernel via propose →
gate (automated verification + HARD-GATE check) → commit (versioned write + rollback to
last_known_good)". **13-gate manifest** ratified: `ENGLISH-ONLY`, `BLAME-EXTERNAL-1`,
`CHANGE-AUDIT-FIRST-1`, `THIN-CLIENT-MANDATE`, `TEST-SEND-EXTERNAL-1`,
`EMAIL-SUBJECT-SPAM-TOKENS-1`, `MANDATE-1-EXECUTION`, `MANDATE-2-PLAN`, `MANDATE-3-REDTEAM`,
`MANDATE-4-SKILL`, `MANDATE-5-PHASES`, `PERSONAL-QNFO-SEPARATION-1`, `GOVERNANCE-KERNEL-SELF`.

`gov_gate_log` proves it is **live and blocking** — 3 rows total:

| ts | decision | reason | actor |
|---|---|---|---|
| 2026-09-11 09:30:12 | **BLOCK** | quality gate: lit_review=0 AND refs=2<5; no_verification_marker | `qnfo-research-exec` |
| 2026-09-11 09:10:43 | **BLOCK** | same | `qnfo-research-exec` |
| 2026-09-01 08:42:48 | APPROVE | kernel ratified autonomously | agent |

**Surviving defect:** one kernel version, ratified once, **3 gate-log entries ever**. Autonomy /
kill-switch state is **split across three places** — `governance_kernel.autonomy_boundary`,
`fleet_deploy_state` key/value (`auto_heal=1`, `enabled=1`), `autonomy_scores` — with no single
evaluator consulted before every L5 action. AF-1 §L3.5's "one table, one evaluator" is unmet and
A7's blast-radius caps are unenforced, which is why D4's unbounded retry is possible.

### D5 — Integration assessment frozen for 47h

`integration_state`: 32 rows, newest **2026-09-11T14:17Z**, writer `qnfo-observability` runs
`*/15 * * * *` → **≈188 missed cycles**. Content mis-sized: `fleet_size: 80` vs actual 55.

### D6 — Intake outruns triage; 42% of signals structurally inert

`idea_proposals`: **496 `new`** (never triaged), 47 `triaged_hold`, 14 `triaged_accepted`.
`signals`: 262 total — 152 consumed, 110 new; **110 (42.0%) carry an empty open-question set
`U`**, so under the signal-organism's own §4.1.2 rule they carry ε=0 and can never fuel L8.

### D10 — AI gateway is the largest live reliability signal (~59,469 logged failures)

`ai_gateway_failures`: **2,611 rows / 397 sweeps**:

| model | cumulative |
|---|---|
| `@cf/baai/bge-base-en-v1.5` (embeddings) | **37,159** |
| `@cf/qwen/qwen2.5-coder-32b-instruct` | **16,674** |
| `@cf/qwen/qwen3.8-27b` | 3,507 |
| `@cf/moonshotai/kimi-k2.6` | 994 |
| `@cf/zai-org/glm-5.2` | 639 |
| `@cf/google/gemma-4-26b-a4b-it` | 396 |
| `@cf/moonshotai/kimi-k2.7-code` | 100 |

The embedding model failing 37k times throttles fleet-wide RAG/ingest. The `[gw-fail]` 24h
auto-close predicate is **structurally unsatisfiable** (append-only at ~48 sweeps/day), so those
tickets cannot close themselves.

### D9 — Research-store data-quality backlog

`living-paper` (904 rows): 451 published, 187 kg-backfill, 157 duplicate, 103 quarantined,
3 superseded, **2 `distributed`**, 1 external_preprint. Only 2 rows carry
`distribution_status='distributed'` although R2 mirroring is a mandatory post-publish gate.
`paper_revision_log`: 38 needs-substantive-revision + 23 quarantined of 100.

### D8 — Deploy surface idle; registry incomplete

Zero deploys in 24h; last success 2026-09-11T10:34Z (**50.7h**). `service_registry` (55 rows:
live 49 + merged 6, 0 missing VERSION) lacks **`health_url`, `owner`, `autonomy_level`, `crons`,
`secrets`** — 4 of 7 Worker-Contract registry fields. 21/55 rows (38%) have no `purpose`.
`fleet_deploy_state` retains `scanerr:` keys for pre-consolidation worker names.

### D11 — Dashboard status thresholds are noise

Nine workers flagged `ERR`, including `fleet-exec` with **1 error in 1,471 requests**. `ERR` is
derived from `err24>0`, which trains operators to ignore the column.

## 3. Withdrawn / corrected claims

1. **`*.q08.workers.dev` is NOT dead — WITHDRAWN.** Google DoH resolves
   `qnfo-ops.q08.workers.dev` → 188.114.96.0/97.0 and `qnfo-ai…` → same. The 404s are a
   **same-account Worker→workers.dev edge artifact** (documented in
   `qnfo-ai-calibration/wrangler.toml` `SVC-BINDING-1` and
   `2026-09-13-CORRECTION-same-account-edge-404.md`). A 404 here is a property of the
   **observer**, not the target. Surviving finding: no `health_url` column, and 55 `base_url`
   values pointing at a surface unprobed since the 2026-09-07 `external-curl` rows (200).
2. **"The self-governing layer does not exist" — WITHDRAWN.** Inferred from the absence of
   tables *named* `policies`/`incidents` — naming a table instead of testing a capability.
   Lesson: **check the capability before declaring a layer absent.**
3. **Silent-cron hypothesis — DISPROVEN as stated, then partially reinstated.** For
   `ai-health-prober` / `qnfo-paper-explainer` the claim remains unverifiable (neither ledger
   instruments them). For the two weekly Monday crons it is now corroborated across four
   sources, with the bootstrap caveat in D12.
4. **D12 evidence grade — UPGRADED then qualified.** Published as "a signal, not proof" on one
   source; now corroborated by `cloud_ops_events`, `report_card_history`, `benchmark_results`.
   Qualified because all records cluster in one 15-minute window on 09-10.

## 4. Honest limits

- Single-vantage, point-in-time D1/CF-API reads under concurrent writers.
- No client-side vantage, no Cloudflare account-settings read, no worker-side logs.
- 209 tables proves fragmentation, not that each table is wrong (`proof_*`, `adr_*`, `email_*`
  are legitimately distinct).
- `fleet_crons.last_fired` may be registry-seeded.
- `autonomy_scores` (11 rows, scored 2026-09-10, next 2026-10-10, overall 3.6/5) is a
  **self-assessment, not a measurement**. It independently names this document's thesis —
  "42/79 island workers", "island outputs do not close into S1", "no redundancy / single ops
  gateway" — but its "81/81 probes" evidence is stale.
- **Strongest counter-argument:** the system is **partially instrumented, not broken**.
  Working loops: `fleet_runs` 476 ok / 5 failed, chat canary 12/12 ok, daily `quality-score`
  sweep firing 09-10/11/12/13, intent queue drained to 0, `qnfo-backlog-exec` deployed 1.2.7
  today, current-cycle probe failure 0.21%, governance kernel actively blocking bad
  publications. The gap is sensing and coordination — not acting, and not governance in
  principle.

## 5. Priority

1. Unify the issue ledgers — `issue_ledger` (305 open) is invisible to every ops tool (A3).
2. Fix the `report_card_history` schema mismatch so SAI has a time series (D16).
3. Extend probes from 10 → 55 via **service bindings** (no public-hostname dependency).
4. Add `health_url` / `owner` / `autonomy_level` / `crons` to `service_registry`.
5. Break the `personal-companion` / `qnfo-cloud-ops` hourly deploy retry (backoff + breaker).
6. Consolidate autonomy/kill-switch state behind one evaluator consulted before every L5 action.
7. Un-freeze `integration_state`; drain the 496 untriaged `idea_proposals`; instrument
   `fleet_runs` and `fleet_crons` for all 40 scheduled workers.
