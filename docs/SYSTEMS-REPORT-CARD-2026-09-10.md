# QNFO Systems-Level Report Card — Fleet Autonomy & Intelligence

Version 1.0 · 2026-09-10 · self-measured (see claim sheet + failure modes)
Canonical: qnfo-ops/docs/SYSTEMS-REPORT-CARD-2026-09-10.md
Owner: QNFO ops · Relation: AUTONOMOUS-FLEET-ARCHITECTURE.md (AF-1), FLEET-MANIFEST.md, fleet.qnfo.org (v1.0.15)

## 0. Purpose and method

This card measures the QNFO fleet AS A SYSTEM (not as a collection of workers) against established
frameworks for machine intelligence and autonomy. It answers one question: how close is the fleet to
the TOP BAND — human-level autonomy, independent thinking, and independent decision-making — and what
objective function drives it there.

Method: self-assessment against external rubrics, scored from live fleet evidence (same-cycle tool
reads), not from aspiration. Every locked claim carries claim / evidence / confidence / status
(FRAMEWORK-DOGFOOD-1). This is a measurement, not a press release; weak scores are reported as-is.

## 1. Rubrics used (external, real frameworks)

| Framework | Measures | Applied to |
|---|---|---|
| SAE J3016 L0-L5 (adapted) | degree of automation of the control loop | A |
| IBM autonomic computing / SEAMS MAPE-K (Monitor-Analyze-Plan-Execute over Knowledge) | self-adaptive loop closure | B |
| IBM self-* properties (self-configuring/healing/optimizing/protecting) | autonomic capabilities | C |
| DeepMind Levels of AGI (Emerging/Competent/Expert/Virtuoso/Superhuman) | general-intelligence ceiling | top band |
| OpenAI 5 levels (chatbots/reasoners/agents/innovators/organizations) | organizational-autonomy ceiling | top band |
| NIST ALFUS (autonomy levels for intelligent systems) | mission/context complexity | A, E |
| Human-in/on/out-of-the-loop taxonomy | where the human sits | A, E |
| METR time-horizon (duration of autonomous operation) | autonomous work horizon | E |
| Anthropic workflows-vs-agents | workflow automation vs genuine agency | E |

TOP BAND (operationalized): L5 human-out-of-the-loop (policy-setting only), DeepMind Expert-or-higher
on the fleet's own domain, OpenAI agents-or-higher, human-on-the-loop for exceptions only. The fleet is
MEASURED against this band — it is not awarded it by default.

## 2. Overall grade

Level: L3 conditional autonomy, with L4 execution elements — a strong self-adaptive system, NOT yet
human-level independent decision-making.

Composite: B- (honest). Strong on verification/safety (A). Moderate on self-healing + closed loops (B).
Weak on drift control (D+), integration (D+), and explicit objective function (C-, the key gap). The
top band (L5) is the target, not the current state.

## 3. Scorecard (10 dimensions)

### A. Autonomy level — L3/L4 (conditional autonomy)
Claim: recurring execution is fully automated (L4); decision-making is self-verifying with
human-on-exception (L3). Evidence: 52 scheduled workers on cloud cron (fleet.qnfo.org live); guard suite
(prompt-store-verify / scheduler-guard / model_guard / adversarial-guard / dr_validate_schema) all exit 0
(2026-09-10); USER-FREE-RESOLUTION-1 standing; v_waiting_on_human=0. Confidence: high. Status: current.
Counter-evidence (not L5): outreach ACTIVATION_AT 2026-09-15 is a dated gate; container-cluster
retirement blocked by open evaluation rows 92/96/97/99; a few migrations are human-anchored.

### B. Closed-loop completeness (MAPE-K) — ~5/8 loops closed
Claim: of the AF-1 eight self-loops (census/heal/improve/audit/govern/publish/promote/optimize), ~5 are
closed with receipts; 3 are open or receipt-less. Evidence: census = fleet-manifest-sweep (weekly cron
42b1988c); heal = qnfo-error-selfheal + fleet-deploy redeploy (this session: qnfo-ops hybrid fix deployed
+ repo reconciled); audit = guard suite + red-team gate; publish = paper-reviser + research-exec drain;
improve = kaizen weekly report. Open/partial: improve (kaizen disposition gap — candidates left proposed
past due, 2026-09-08), govern (register human rows), optimize (fleet-calibrator receipts partial).
Confidence: medium (loop closure inferred from crons + logs, not exhaustively receipt-counted).

### C. Self-healing — B+/A-
Claim: the fleet self-corrects deterministic failures without a human. Evidence: 5-guard suite exit 0;
qnfo-error-selfheal (hourly cron, deduped agent_issues, re-arms fixed errata classes); deploy-verify-version;
this session's self-correction (stale repo hybrid landmine found + fixed + redeployed qnfo-ops v2.9.3 in-session).
Confidence: high. Limit: healing cannot reach ~65 unversioned workers (no VERSION/health contract to heal
against) — heal is gated by the drift problem (H).

### D. Self-improvement — C+
Claim: a closed improvement loop exists (idea intake -> triage -> exec -> publish -> revise), but the
meta-loop (improving the improver) is partial. Evidence: idea_proposals multi-source intake (edge form +
auto-miner + auto-scan); paper-reviser auto-revision (>=2 versions per publication); kaizen weekly report.
Gap: kaizen candidates can sit proposed past their register due (KAIZEN-DISPOSITION-GAP-1).

### E. Independent decision-making — C+ (horizon hours-to-days)
Claim: the fleet makes + executes operational decisions autonomously; strategic/reversible decisions remain
dated-gated or human-anchored. Evidence: autonomous outreach engine (OUTREACH-ENGINE-LIVE-1, global 8/day cap,
per-domain 3/day, warm-up to 09-15); autonomous disposition (USER-FREE-RESOLUTION-1); identity-bound surfaces
cancelled-with-monitor. METR-style horizon: hours-to-days (cron-driven), not weeks.

### F. Self-model / situational awareness — C
Claim: single-source-of-truth self-model exists (registry-as-truth) but is incomplete/inaccurate.
Evidence: service_registry 80 rows vs 79 live (1 ghost qnfo-wrangler-test); ~65/80 unversioned; FLEET-MANIFEST
stale (65 vs 79 live). Multiple ledgers disagree (A3 violation). Confidence: high (direct D1 reads).

### G. Verification & safety — A
Claim: verify-before-trust + blast-radius + kill switches + cost ceilings + adversarial checks are
best-in-class. Evidence: 5-guard suite exit 0; axioms A5/A7/A9; AI spend $18.08/$90 (2026-09-06, memory);
adversarial-reasoning blocks in 6 core workers; SERVER-SIDE-EXEC-100-1 (no client code execution).

### H. Drift control (Lyapunov / attractor distance) — D+
Claim: drift is the weakest signal — small drift amplifies because it is under-damped.
Evidence: ~65/80 unversioned (invisible to drift management); 1 ghost; deployed-current mirror drift + repo-vs-deploy
drift (the hybrid landmine) found + fixed this session. Chaos terms: positive-Lyapunov regime on version
discipline — drift does not self-damp.

### I. Integration (graph + contract) — D+
Claim: the fleet is a sparse near-star graph; most workers are un-integrated leaves; declared wiring is incomplete.
Evidence (fleet.qnfo.org/api/integration, live): 80 registered / 49 declared edges / density 0.0078 / 42 islands /
16 sinks; service_registry deps under-populated (empty or free-text). Components function; system integration is
the gap (the operator's exact observation).

### J. Objective function — C- (gap)
Claim: no unified, computable objective function drives all eight loops; the Watchmaker Index is a success
metric but not a shared optimization target. Evidence: Watchmaker Index defined in AF-1 (share of recurring ops
needing a human) but not computed as a live scalar feeding every loop; loops optimize locally, not against a
shared fitness function. Confidence: high (absence of evidence).

## 4. Systems-theory integration (lessons applied)

- Closed loops with receipts (cybernetics) -> B; the objective must reward loop closure.
- Single source of truth (A3) -> F; registry vs live vs manifest disagreement is the canonical failure.
- Attractor + Watchmaker Index -> the fleet's objective is distance to the healthy attractor
  (all versioned, /health OK, registry == live, wired).
- Lyapunov drift -> H; unversioned/ghost counts are the positive-lambda signal to damp.
- Edge of chaos -> A/G; adaptive (registry-driven) but bounded (kill switches, cost ceilings, blast radius).
- Fractal self-similarity -> the same drift/integration anti-pattern recurs at worker, subsystem, fleet scale;
  this card uses one lens at every layer.

## 5. Objective function proposal (drives continuous improvement)

Define a scalar fleet-autonomy fitness F(t), computed from the ledgers every cycle, that all eight loops
locally optimize against:

F = w1 * loop_closure_rate - w2 * drift_count - w3 * human_interventions - w4 * cost_overrun - w5 * integration_gap + w6 * throughput

- loop_closure_rate = closed loops / 8 (B)
- drift_count = unversioned + ghost + mirror-drift (H)
- human_interventions = v_waiting_on_human + dated-gated migrations (E)
- cost_overrun = max(0, spend - $90/30d) (G)
- integration_gap = islands + unregistered + declared-vs-actual mismatch (I)
- throughput = publications + deploys + ideas triaged (D)

Each loop reports its contribution to F with a receipt; the kaizen loop reviews F weekly and proposes the
next-highest-marginal-improvement action (gradient ascent on F). STATUS: proposed, not implemented —
implementing F as a computed ledger column + a dashboard card is the top next action.

## 6. Roadmap to the top band (L5, human-out-of-the-loop)

1. Normalize service_registry.version to semver (closes ~65 blind spots) — highest leverage, enables H.
2. Implement the objective function F as a computed scalar (dashboard card + weekly kaizen review).
3. Wire the static binding matrix into the dashboard so declared-vs-actual integration drift is computable (I).
4. Close the 3 open loops (kaizen disposition, govern register, calibrator receipts) (B).
5. Convert dated-gated items (outreach ACTIVATION_AT, retirement evaluation rows) to autonomous triggers with
   kill switches (moves A toward L4/L5).

## 7. Claim sheet (FRAMEWORK-DOGFOOD-1)

| Claim | Evidence | Confidence | Status |
|---|---|---|---|
| Overall grade B- / L3-L4 | scorecard section 3, live reads this cycle | medium (self-measured) | current |
| 5-guard suite exit 0 | same-turn tool runs 2026-09-10 | high | current |
| 80 reg / 79 live / 1 ghost / 0 unregistered | D1 service_registry + live list | high | current |
| ~65 unversioned (drifting 65-67) | D1 service_registry.version not semver | high | current |
| density 0.0078 / 42 islands / 16 sinks | /api/integration live | high | current |
| qnfo-ops v2.9.3 hybrid removal deployed | /health + probe + repo a6f2f14 | high | current |
| ~5/8 self-loops closed | crons + logs, receipt-count inferred | medium | current |
| objective function not implemented | absence-of-evidence search | medium | current gap |

## 8. Adversarial / failure modes (this card could be wrong)

- Self-measurement bias: the system grades itself (the grader is the graded, A6). A third-party audit could
  differ. Mitigation: every score tied to a same-turn read + confidence label.
- Rubric mismatch: SAE L-levels (vehicles) and DeepMind levels (general AI) were designed for other domains;
  mapping them to a Cloudflare fleet is an analogy, not a validated instrument — level assignments are interpretive.
- "~5/8 loops closed" is inferred from crons + logs, not exhaustively receipt-counted; the true number could be 4 or 6.
- Evidence is point-in-time (2026-09-10); the card will go stale unless F is computed continuously.
- The objective-function weights (w1..w6) are unspecified and uncalibrated; the proposal is directional.
