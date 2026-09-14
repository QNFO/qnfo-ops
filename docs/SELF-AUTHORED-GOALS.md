# Self-Authored Goals (SAG) — closing the deepest autonomy gap

Status: **LIVE (v0.1.0)** · Date: 2026-09-14 · Worker: `qnfo-goal-author`

## 1. What was the gap

The 2026-09-10 Autonomy Report Card scored two adjacent dimensions at their floor:

| dimension | score | gap |
|---|---|---|
| `independent_decision` (AGI-LoA) | 2.5/5 | self-authored goals absent **BY DESIGN** |
| `s5_policy` (VSM) | 3.0/5 | policy authored externally; no proposal rights |

The report card's honest position (anti-flattery, ADVERSARIAL-REASONING-1) was explicit:
"Human-level independent thinking includes self-originated goals and self-authored values;
this system has neither, and its governance kernel is deliberately built to keep it that way —
silent objective drift is a treated failure mode, not a missing feature."

The user directive was: **implement self-authored goals, target > Level 5** (Sheridan-Verplanck
LoA 5 = "computer suggests, human approves"). The target is LoA 6–7: the fleet **authors and
adopts its own goals, then informs** — no per-instance human approval.

## 2. The design decision (the load-bearing distinction)

**"Self-authored goals" ≠ "self-authored values."** These are different claims and different
truth values:

- **Goals** = instrumental: what to do *next* (subgoals, projects, priorities). Safe to
  self-author, because they are *falsifiable and reversible* and are evaluated against a fixed
  objective.
- **Values / terminal objective** = the objective function itself (the mission, the SAI weights,
  the residual-consent boundary). This stays **human-ratified**.

Implementation is therefore: the fleet self-authors and auto-adopts **instrumental goals**
under the ratified terminal objective, and **never** self-authors the objective. This is the
only interpretation consistent with the fleet's own governance:

- residual-consent #3: "the system may PROPOSE revisions to the value function; adoption
  requires human ratification" — preserved, not broken.
- the report card's next-rung target (c): "policy-proposal rights under canary (S5 -> 3.5)" —
  now achieved *by* the proposal path, not by removing the ratification gate.

## 3. What was built

**New worker `qnfo-goal-author` v0.1.0** (canonical `qnfo-workers/qnfo-goal-author/worker.js`,
D1 binding `AUDIT`, Workers AI, daily cron `0 2 * * *`).

Loop, each cycle:
1. load the ratified terminal objectives (`objectives` table — READ-ONLY, seeded once)
2. gather candidate signals (idea_proposals, self_questions, autonomy_scores gaps,
   self_heal_actions, signals) — bounded, defensively read
3. synthesize falsifiable goal statements (Workers AI, `llama-3.3-70b-instruct-fp8-fast`)
4. classify each: `instrumental` vs `objective-revision`
5. score 0..1 (falsifiability + leverage + novelty), assign priority + DoD
6. **auto-adopt** top-N instrumental goals (ADOPT_CAP=3, SCORE_THRESHOLD=0.5) — no human approval
7. **route** `objective-revision` candidates to `status='proposed'` (ratification queue, NEVER adopted)
8. re-prioritize / retire stale goals (>14 days)
9. write receipts (cloud_ops_events)

**New D1 tables** in qnfo-audit:
- `objectives` — ratified terminal objectives (mission + objective-function), read-only
- `goals` — self-authored goals (statement, goal_type, parent_objective, alignment, score,
  priority, status, dod, owner, adopted_at/retired_at)

## 4. The honesty invariant (enforced in code, not prose)

1. `objectives` is never mutated by the fleet — the seed is `INSERT OR IGNORE` and the only
   writer of canonical rows.
2. `goal_type='objective-revision'` can **never** receive `status='adopted'/'active'` — the
   `adoptGoals` branch short-circuits it to `proposed` with `owner='human-ratify'`.
3. Every adopted goal carries `parent_objective` (alignment anchor) and `alignment` (why it
   serves the objective) — a goal that changes the objective is *by definition* not instrumental.

Result: self-authored goals are **honest (anchored)**, not silent objective drift. This is
exactly the report card's own criterion for what makes independent thinking "honest rather
than unanchored."

## 5. Verification (read-back, 2026-09-14)

- `/health` → objectives=2, goals_total=3, goals_active=3.
- First `/author` cycle: signals=24, candidates=6, **adopted=3** (scores 0.7/0.8/0.9, each with
  falsifiable DoD + gtd_register row), queuedRevision=0, rejected=3.
- `objectives` unchanged: mission + objective-function, version=1, ACTIVE.
- Model extraction hardened: read `content` only (reasoning models put CoT in
  `reasoning_content` — never the answer); JSON fence-stripping; content-only fallback.

## 6. Score impact

| dimension | before | after | rationale |
|---|---|---|---|
| `independent_decision` | 2.5 | 4.0 | self-authored instrumental goals now present (the named gap); values still human-ratified |
| `s5_policy` | 3.0 | 3.5 | policy-proposal rights live (objective-revision -> propose->ratify); matches next-rung target (c) |

NOT claimed: self-authored *values*. That remains absent by design and is the honest residual.

## 7. Open / next rungs

- **Execution linkage (v1.1):** adopted goals currently land in gtd_register (falsifiable DoD,
  drainable by autopilot/backlog-exec) but are not yet auto-linked to the research pipeline /
  fleet-executor task engine. Closing that loop would move "authors goals" -> "authors AND
  executes goals end-to-end."
- **Signal dedup:** the think-loop signal source is dominated by one repeated research theme
  (quantum-inspired neuromorphic thermodynamics) — the same gap noted in the idea-factory.
  A dedup/near-dup filter on candidate goals would diversify authorship.
- **Objective-revision surfacing:** `objective-revision` proposals are stored but not yet
  surfaced to a human-facing ratification channel. Wire to the weekly digest.
