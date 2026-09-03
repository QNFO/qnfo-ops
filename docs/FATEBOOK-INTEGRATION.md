# QNFO Fatebook Integration - Strategy and Options

> Version 1.0 (2026-09-03) - Owner: QNFO - Status: EXPLORED / PLANNED (no Fatebook account or API key yet)
> Claim: Fatebook's public API (10 procedures under /v0/*) plus the community fatebook-mcp MCP server give
> QNFO a low-friction public calibration ledger for probability-bearing research claims, creatable and
> resolvable from a script or a Cloudflare Worker, with every write path gated by one account-level API key.
> Evidence: https://fatebook.io/api/openapi.json fetched 2026-09-03 (8 JSON procedures + createQuestion /
> getQuestion documented on the api-setup page); live probes 2026-09-03 returned HTTP 401 on
> /v0/createQuestion, /v0/getQuestion, /v0/getQuestions with an invalid key (endpoints live, key-gated) and
> HTTP 404 on /v0/countForecasts for an unknown userId; api-setup page and both MCP READMEs (an1lam/
> fatebook-mcp on PyPI, dcm31/mcp-fatebook v2 on Val Town) reviewed. No end-to-end write test was possible:
> grep of local stores (2026-09-03) found zero prior Fatebook references and no key in the environment.
> Confidence: high on API surface and integration paths; unverified on live writes (key required).
> Status: exploration complete; implementation gated on credentials + design decisions in section 9.

---

## 1. Objective

Give QNFO a public, time-bound, scored record of its probability-bearing claims so forecasting skill
becomes measurable rather than rhetorical. QNFO publications already carry falsifiable framing
(disconfirmation criteria, pre-registration discipline, honest-correction culture). Fatebook is the
natural external home for the probability layer of those claims: one account-level key, a dead-simple
create-by-URL API, a public question board, and a native calibration scoring loop.

This document inventories what Fatebook exposes (verified 2026-09-03), compares the integration paths
(direct REST, MCP, platform add-ons, QNFO cloud-native design), and proposes a governed calibration-ledger
design consistent with QNFO standing mandates (honest measurement, no fabrication, no spam, no branded
prose, cloud-native recurring functions).

## 2. Platform and API surface (verified 2026-09-03)

### 2.1 Identity and auth model

- One account at fatebook.io; the API key is generated at https://fatebook.io/api-setup after sign-in.
- The key is passed as `apiKey` (query parameter on GETs, JSON body field on POST/PATCH/DELETE). The
  OpenAPI file also declares a Bearer scheme, but every documented endpoint uses the inline `apiKey`.
- Unauthenticated or invalid-key calls return HTTP 401 (verified on three endpoints).
- `https://fatebook.io/api/openapi.json` is public and current - a useful machine-readable contract.

### 2.2 Endpoint inventory

| Endpoint | Method | Purpose | Key required | Notes |
|---|---|---|---|---|
| /v0/createQuestion | GET | Create a question from a plain URL | yes | title + resolveBy + optional forecast(0-1); optional tags (repeat), sharePublicly, shareWithLists (repeat), shareWithEmail (repeat), hideForecastsUntil |
| /v0/getQuestion | GET | Fetch one question by ID | yes | ID = part of the question URL after "--" |
| /v0/getQuestions | GET | List questions (yours, or public board) | yes | filters: resolved, unresolved, readyToResolve, resolvingSoon, filterTagIds, searchString, theirUserId, filterTournamentId, filterUserListId, sortEarliestFirst, limit (default 100), cursor |
| /v0/addForecast | POST | Add probability 0-1 | yes | optionId only for multi-choice questions |
| /v0/addComment | POST | Attach reasoning / notes | yes | useful for DOI + criterion links |
| /v0/resolveQuestion | POST | Resolve YES/NO/AMBIGUOUS (binary) or AMBIGUOUS/OTHER/$OPTION (multi) | yes | only your own questions; questionType BINARY etc. |
| /v0/editQuestion | PATCH | Change title / resolveBy / notes | yes | resolveBy is date-time (ISO 8601) |
| /v0/setSharedPublicly | PATCH | Toggle public link + unlisted visibility | yes | unlisted = hidden from fatebook.io/public |
| /v0/deleteQuestion | DELETE | Delete a question | yes | query params |
| /v0/countForecasts | GET | Count a user's forecasts | no (public) | returns numForecasts + userName; 404 for unknown userId |

### 2.3 Behavior notes

- `resolveBy` accepts `YYYY-MM-DD` but defaults to 00:00 UTC (the day BEFORE a local-noon resolver's
  intent). Pass ISO-8601 with an explicit offset (e.g. 2026-12-31T23:59+00:00) when timezone matters.
- createQuestion/getQuestion are NOT listed in the OpenAPI file even though they are live; OpenAPI covers
  the richer JSON procedures (getQuestions, addForecast, addComment, resolve, edit, setSharedPublicly,
  delete, countForecasts).
- Resolution is owner-only. Forecasts can be added by others if the question is shared, but QNFO's
  calibration ledger only needs owner forecasts.

## 3. Integration options

### Option A - Direct REST (thinnest)

One `curl`/fetch to the createQuestion URL is a complete question create (that is how the official iOS
shortcut works). All other operations are simple JSON calls. Fits any runtime: a qnfo-ops script, a
Cloudflare Worker, a cron one-liner. No dependency beyond the key.

### Option B - MCP server (fatebook-mcp)

- an1lam/fatebook-mcp (PyPI, MIT, Python 3.13+; uvx auto-provisions the interpreter). Stdio server; tools
  mirror the API: create/list/get-details/addForecast/addComment/resolve/edit/delete/count. Configured with
  `command: uvx`, `args: [fatebook-mcp]`, `env: {FATEBOOK_API_KEY: ...}`.
- DeepChat precedent: mcp-settings.json already runs stdio servers via uvx (arxiv-mcp-server). Adding a
  fatebook entry is mechanically identical; it would slot into the MCP fleet (file is source of truth,
  MCP-AUTOAPPROVE-PARITY-1 applies after restarts).
- dcm31/mcp-fatebook on Val Town (v2) is an HTTP/remote variant; less transparent than the PyPI package,
  and remote execution of key-bearing code warrants extra caution.
- Cost/benefit: interactive "create a question / what is my calibration" conversations in-session; not
  needed for batch automation.

### Option C - Platform and user-made integrations (not for QNFO automation)

Chrome/Firefox extension, Slack, Discord, Beeminder, embed-in-website, PredictionBook and spreadsheet
import/export. User-made: Obsidian plugin (GarretteBaker/obsidian-fatebook), iOS shortcut, Emacs plugin
(sonofhypnos/fatebook.el), Alfred workflow (Calebp98/alfred-fatebook-workflow). Relevant only if a human
wants to log forecasts from the browser or editor; none are part of a QNFO pipeline.

### Option D - QNFO cloud-native calibration ledger (recommended)

Small script + optional Worker that owns QNFO's Fatebook questions as data, keyed off the existing
publication/claims stores. Details in section 4. This is Option A plus QNFO governance, not a new
platform dependency.

### 3.1 Comparison

| Criterion | A direct REST | B MCP server | C platform add-ons | D QNFO ledger |
|---|---|---|---|---|
| Effort to first question | minutes | minutes | minutes (human) | hours (script + gates) |
| Recurring automation | yes (script/cron) | no (interactive) | no | yes (scheduled worker) |
| Reproducible audit trail | yes (repo script) | partial | no | yes (D1/registry link) |
| Calibration reporting | manual | manual | manual | automated feed to scorecard |
| In-session agent control | no | yes | no | optional via same script |

Recommendation: Option D as the durable design, built on Option A mechanics; register Option B only if
in-session question management is wanted (cheap, but gated on the same key).

## 4. Recommended design: QNFO calibration ledger

Concept: every published QNFO claim that carries an explicit probability and a resolution condition gets
a Fatebook question. The question is the public, dated, scored representation of the claim; the paper
record stays canonical for evidence. Forecasts are owner forecasts only (no crowd). Resolution follows
the claim's own disconfirmation criterion or the stated date, whichever comes first.

### 4.1 Data mapping

| Fatebook concept | QNFO source | Rule |
|---|---|---|
| title | claim sentence (paper abstract/claim block) | plain prose, no internal tokens (PUBLICATION-BRAND-LANGUAGE-1) |
| forecast | stated probability (0-1) | must equal the number in the published claim |
| resolveBy | claim resolution date or disconfirmation decision date | ISO-8601 with offset; stored next to the claim |
| tags | program/program_id, slug | e.g. tag "jpcub", "uia" - searchable in getQuestions |
| addComment | paper DOI + criterion pointer | "DOI 10.5281/zenodo.XXXX - disconfirmation criterion: ..." |
| resolved | outcome of the criterion | YES/NO/AMBIGUOUS per the claim's own verdict |
| sharedPublicly | claim was already public | default yes for published claims |

### 4.2 Pipeline (all recurring functions in the Cloudflare layer per CLOUD-FRONTEND-ONLY-1)

| # | Function | Where | Cadence | Trigger |
|---|---|---|---|---|
| P1 | claim -> question create (script/worker reads claims store for published probability claims, creates Fatebook question if absent, stores fatebook_question_id beside the claim) | qnfo-cloud-ops subprocess or a qnfo-fatebook-sync worker | weekly Mon 04:05 UTC | cron |
| P2 | resolution sweep (for questions past resolveBy or whose claim flipped resolved, call resolveQuestion and log outcome) | same subprocess/worker | weekly Mon 04:10 UTC | cron |
| P3 | calibration digest (count resolved vs forecast bins; Brier-ish score per program) written to qnfo-audit + included in the weekly P7 scorecard email | qnfo-cloud-ops jobVisibility extension | weekly Mon 07:30 AMS | cron |
| P4 | human-in-loop approval queue for any question that should be public/unlisted or whose title needs rewording | none (log to qnfo-audit for review) | as produced | event |

Phase 1 ships P1/P2 only, pointed at a small curated set of flagship claims; P3 joins after one full
resolution cycle proves data quality (same gate philosophy as the version-radar queue).

## 5. Governance and integrity gates

- FATEBOOK-PUBLIC-PROSE-1 (HARD): question titles/comments are public-facing publication prose. Ban
  internal register/ledger/honesty tokens (PUBLICATION-BRAND-LANGUAGE-1), meta-narration
  (PUBLICATION-META-PROSE-1), and AI-telegraph tells (ANTI-TELEGRAPH-1). A question is not marketing; it
  is a dated claim.
- FATEBOOK-PROBABILITY-FIDELITY-1 (HARD): the forecast on Fatebook MUST equal the number published in the
  claim. Discrepancy = fabrication signal. Verified by the script reading both stores before create.
- HONEST-ONLY: calibration numbers are read from Fatebook responses and qnfo-audit rows, never invented.
  Worker-invocation counts remain self-health only (IMPRESSIONS-ZONE-NOT-WORKER-1).
- NO-SPAM: no mass following/commenting/forecasting on other users' questions; no question spam on the
  public board. QNFO questions are created unlisted until reviewed (setSharedPublicly after the P4
  approval row).
- Test discipline: any end-to-end test runs on QNFO's OWN account questions, never another user's; test
  questions are deleted or resolved immediately (mirrors TEST-SEND-EXTERNAL-1).
- Credential storage: the Fatebook API key lives in the Worker secret store AND a redundant local mirror
  (per OSF-CREDENTIAL-REDUNDANCY-1 pattern); never committed to the repo.
- MCP parity (only if Option B is registered): mcp-settings.json is source of truth; after any app restart
  re-verify file == running-app DB (MCP-AUTOAPPROVE-PARITY-1).

## 6. Roadmap and decision points

| Phase | Deliverable | Gate / evidence | Decision needed |
|---|---|---|---|
| P-A | Fatebook account + API key | key works on a real create (one own-account test question) | user creates account + provides key (section 9) |
| P-B | qnfo-ops/scripts/fatebook_question.py wrapper | create/list/resolve of the test question, exit 0 | none |
| P-C | (optional) fatebook MCP in mcp-settings.json | file==DB after restart; live tool call | user wants in-session control |
| P-D | qnfo-fatebook-sync worker or cloud-ops subprocess | /health reports cadence; D1 row for each created/resolved question | P-A + P-B clean |
| P-E | calibration digest in weekly scorecard | qnfo-audit table fed on resolution | one full resolved cycle |

## 7. Risks and guardrails

- Public questions are dated claims that can be scored against QNFO. Guardrail: create unlisted until a
  human row approves publication; resolution logic is deterministic from the claim record, not ad hoc.
- API key leakage. Guardrail: Worker secret + local mirror; rotate on any exposure; test-after-rotate.
- Over-forecasting (claiming probabilities for non-probabilistic statements). Guardrail: only claims with
  an explicit published probability and a resolvable criterion are eligible; the eligibility check is part
  of P1.
- Fatebook is a third-party service (Sage Future Inc). Guardrail: the ledger is a mirror of QNFO's own
  claims record; loss of the service never loses the underlying evidence (claims stay canonical in QNFO
  stores).

## 8. Claims and evidence

| Claim | Evidence | Confidence | Status |
|---|---|---|---|
| Fatebook API surface = 10 /v0/* procedures | openapi.json (8 JSON) + api-setup page (create/get, GET) fetched 2026-09-03 | high | verified |
| Write endpoints require a valid API key | HTTP 401 on createQuestion/getQuestion/getQuestions with invalid key, 2026-09-03 | high | verified |
| countForecasts is public but user-scoped | HTTP 404 for unknown userId without a key | medium | verified (boundary only) |
| No Fatebook key or prior reference in QNFO environment | grep of local stores + conversation search, 2026-09-03 (zero hits) | high | verified |
| fatebook-mcp (PyPI) runs via uvx with env FATEBOOK_API_KEY | README reviewed; matches existing arxiv-mcp-server stdio pattern in mcp-settings.json | high | verified (not executed) |
| End-to-end create/forecast/resolve works as documented | NOT TESTED - no account/key in environment | n/a | unverified |

## 9. Open decisions for the user

1. Create a Fatebook account and supply an API key (required for every path).
2. Public vs unlisted default for QNFO questions (recommended: unlisted until reviewed).
3. Scope of the pilot claim set (recommended: flagship papers with explicit probabilities only).
4. Whether to also register the fatebook-mcp server for in-session use.

---

*Canonical repo: QNFO/qnfo-ops (docs/FATEBOOK-INTEGRATION.md). Exploration basis: fatebook.io/api-setup,
fatebook.io/api/openapi.json, github.com/Sage-Future/fatebook, an1lam/fatebook-mcp, dcm31/mcp-fatebook v2.
Aligned with docs/EXPERIMENTATION-PROGRAM.md (honest measurement) and docs/OUTREACH-AUTOMATION-STRATEGY.md
(no-spam, activation date gates).*
