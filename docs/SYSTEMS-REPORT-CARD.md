# QNFO Systems-Level Report Card - Autonomy & Intelligence

Status: canonical | Version 1.0 | 2026-09-10 | Owner: QNFO ops
Canonical: qnfo-ops/docs/SYSTEMS-REPORT-CARD.md
Companions: AUTONOMOUS-FLEET-ARCHITECTURE.md (AF-1); SERVER-SIDE-EXEC-CLIENT-MATRIX-2026-09-09.md
Live surface: fleet.qnfo.org ("Systems report card" section; /api/integration)

## 0. Purpose

Codify the fleet's OBJECTIVE FUNCTION for continuous self-improvement, scored against established,
citable frameworks for machine autonomy and intelligence. The report card's TOP of scale is
HUMAN-LEVEL autonomy and independent thinking / decision-making. The fleet is scored honestly - it
is not at the top - and the gap between current score and top of scale IS the objective function
the fleet drives toward.

## 1. The frameworks (external, citable)

| Framework | What it measures | Top of scale | Source |
|---|---|---|---|
| Sheridan-Verplanck Levels of Automation | Human-vs-machine decision authority, 10 levels | LoA 10: computer does everything, human ignored | Sheridan & Verplanck 1978 |
| Parasuraman-Sheridan-Wickens 4-stage | Which cognitive stages are automated (acquire, analyze, decide, act) | all 4 stages autonomous | IEEE Trans. SMC-A 2000 |
| Beer Viable System Model (VSM) | Organizational viability via 5 systems S1-S5 | S1-S5 closed; S5 policy internalized | Beer, Brain of the Firm 1972 |
| OpenAI Levels of AI | Intelligence ladder, 5 levels | L5 Organizations | OpenAI 2024 |
| DeepMind Levels of AGI | Performance x generality, 6 levels | Virtuoso / ASI | Morris et al. 2024 |
| ALFUS | Autonomy of unmanned systems (mission complexity, env difficulty, human independence) | full human-independence | NIST / SAE |
| OODA loop | Decision-cycle completeness (Observe-Orient-Decide-Act) | closed, fast, self-reinitiating | John Boyd |
| Legg-Hutter Universal Intelligence | Formal intelligence = goal-achievement across environments | unbounded | Legg & Hutter 2007 |

## 2. The rubric - five dimensions

| Dimension | Framework | 0 (absent) | 5 (human-level) |
|---|---|---|---|
| Decision authority | Sheridan-Verplanck LoA | human does everything | computer does everything; informs or ignores |
| Cognitive automation | Parasuraman-Wickens | no automation | acquire+analyze+decide+act all autonomous |
| Organizational viability | Beer VSM | S1 only | S1-S5 closed; S5 policy internalized |
| Intelligence level | OpenAI/DeepMind | L1 chatbot | L5 organization (multi-agent org) |
| Decision-cycle closure | OODA | no loop | closed loop, near-real-time, self-reinitiating |

Each dimension is a ladder; the composite places the fleet on a single autonomy-intelligence
spectrum. The rubric is deliberately qualitative: a false-precision composite number would violate
A8 (honesty).

## 3. Current score (honest, 2026-09-10)

- Decision authority - LoA 8. Routine operations (crons, radars, syncs, self-heal filing, deploys)
  execute and inform; novel / high-blast-radius actions are gated by A6 (no self-redeploy) and A7
  (blast radius). Not LoA 10.
- Cognitive automation - 3.5/5. Observe, Orient, Act are autonomous; Decide is partially gated
  (human policy + A6/A7 approvals).
- Viability (VSM) - 3/5. S1 (78 workers) + S2 (fleet-scheduler, queues, handoffs) + S3
  (census/audit/self-heal/calibration) present. S4 (intelligence/future) partial (radars + idea
  intake exist but are not a closed strategic loop). S5 (policy/identity) EXTERNAL (human
  directives + immutable gates).
- Intelligence - L3 Agents. Multi-agent, tool-using, self-correcting, server-side. Approaching L4
  (Innovators) via the autonomous research pipeline (idea -> triage -> exec -> publish). Not L4 yet:
  novelty judgment and independent hypothesis generation are not autonomous.
- Decision cycle - 4/5. Closed, 15-minute scheduler cadence, receipts in the run ledger; not
  real-time and not fully self-reinitiating across every loop.

COMPOSITE: "Autonomous operations with human policy" (LoA 8 / AGI L3 / VSM S1-S3+S5 / OODA closed).

## 4. The objective function (drives continuous improvement)

Maximize autonomous goal-achievement across the fleet's task environment (Legg-Hutter), measured by:

  (a) Watchmaker Index -> 0   (share of recurring operations requiring a human)
  (b) mean-time-to-human-intervention -> +inf
  (c) self-heal success rate -> 1
  (d) drift divergence -> 0   (ghost + unregistered + unversioned; the chaos/Lyapunov signal)

Subject to the values that bound autonomy: A3 single source of truth, A6 separation of powers,
A7 blast-radius limits, A8 honesty (no fabrication), A9 cost ceilings, A10 idempotence.

Adversarial note: "human-level autonomy" is NOT "unbounded autonomy". A human organization is itself
bounded (law, board, ethics). The correct TOP is autonomy with INTERNALIZED values - S5 policy moves
from EXTERNAL (human directives) to INTERNAL (the system sets and enforces its own invariants). That
is the L3 -> L5 transition: the fleet internalizes the gates it currently receives as directives.

## 5. The gap -> next level (concrete, ranked)

1. Normalize service_registry.version to semver - 67 of 80 rows are unversioned or non-semver
   ("fabric-...", "1.8", "1.2-cors-fixed", null). Highest-leverage drift fix: it un-blinds drift
   management to 84% of the fleet at once (chaos damping, negative Lyapunov).
2. Close S4 - make the idea/radar/scan loop STRATEGIC (feed the objective function), not just
   operational. This is the L3 -> L4 (Innovators) step.
3. Internalize S5 - migrate gates from external directives to self-enforced invariants with
   self-audit receipts, so high-blast-radius actions move LoA 5-6 -> 8-9 without losing A6/A7.
4. Wire the static binding matrix into the dashboard so edges reflect ACTUAL bindings, not just
   declared deps (the 42 islands are currently a declared-wiring lower bound).
5. Drive drift divergence to zero and hold it there (the chaotic-regime exit criterion).

## 6. Systems + chaos theory lessons - integrated fleet-wide

| Lesson (theory) | Operationalized in the fleet | Live dashboard metric |
|---|---|---|
| Emergence: integration edges are first-class | service_registry deps graph; AF-1 Worker Contract | edges, density, islands, hubs |
| Closed loops with receipts (cybernetics) | 8 self-* loops; run ledger fleet_runs | self-heal count, deploys, run ledger |
| Single source of truth (A3) | registry-as-truth; ghost/unregistered reconciliation | ghost, unregistered |
| Interface/contract drift | VERSION + /health + binding names | unversioned count |
| Sensitive dependence (chaos) | stale-mirror regression class (canonical: qnfo-ops 1.9.8 landmine) | deployed-vs-repo drift |
| Attractor distance | Watchmaker Index = distance to healthy attractor | human-open count |
| Lyapunov drift amplification | unversioned/ghost = amplifying drift | drift divergence |
| Self-organized criticality | queue depth + consolidation tiers | backlog/pending counts |
| Edge of chaos | adaptive (registry-driven) but bounded (A6/A7/A9) | LoA level + kill switches |
| Fractal self-similarity | same anti-pattern at every layer | kaizen anti-pattern ledger |

## 7. Claim sheet (FRAMEWORK-DOGFOOD-1)

| Claim | Evidence | Confidence | Status |
|---|---|---|---|
| Frameworks listed are real, citable measures of machine autonomy/intelligence | published sources (Sheridan & Verplanck 1978; Beer 1972; OpenAI 2024; Morris et al. 2024; Legg & Hutter 2007) | high | verified |
| Fleet composite = LoA 8 / L3 Agents / VSM S1-S3+S5 | registry + live dashboard data (78 workers, self-heal, 0 human-open, 67 unversioned) | medium-high | measured 2026-09-10 |
| 67/80 registry rows are unversioned/non-semver | /api/integration live | high | measured 2026-09-10 |
| The fleet is NOT human-level | no independent novel-hypothesis loop; S4 partial; S5 external | high | assessed 2026-09-10 |
