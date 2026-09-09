# ops-exec: 100% Server-Side Execution Across All Chat Clients

Date: 2026-09-09 · Generator: qnfo-ops endpoint (service v2.7.0) · Status: GENERATED canonical instruction text — live application requires device-side store writes + worker code deploy (see section 7).

## 1. Directive (WHAT / WHY)

Operator directive 2026-09-09: 100% server-side code execution — ONLY. No local tool code, no local tool calls — for four client classes against the ops-exec endpoint:

1. DeepChat Windows
2. ChatBox Windows
3. ChatBox Android
4. SannaBot Android

Every code/tool operation executes on Cloudflare inside qnfo-ops. Clients are dumb terminals: render text, never execute.

## 2. Endpoint contract (ground truth: service registry 2026-09-09T14:30:03Z)

| Field | Value |
|---|---|
| service / kind | qnfo-ops / worker, version 2.7.0 |
| base_url | https://qnfo-ops.q08.workers.dev |
| chat route | POST /v1/chat/completions (OpenAI-compatible); /v1/responses supported; GET /v1/models |
| models | ops-exec (QNFO-OPS/ops-exec, default) · deepseek-v4-flash (explicit relay only) |
| auth | Bearer OPS_ROUTER_AUTH_KEY (secret — reference by name only, never echo) |
| audit | every request -> qnfo-audit.ops_ai_log with source + strategy |
| compute | run_code isolated JS + all data tools, server-side only |

## 3. System-prompt gate paragraph (paste-ready; v4.21 candidate)

MANDATORY (2026-09-09, system-prompt v4.21 / kaizen v2.142 / SERVER-SIDE-EXEC-100-1): preserve the four-client 100%-server-side-execution gate (operator directive 2026-09-09: 100% SERVER-SIDE CODE EXECUTION ONLY across DeepChat Windows, ChatBox Windows, ChatBox Android, SannaBot Android — no local tool code, no local tool calls, no finish_reason=tool_calls to any client) — SERVER-SIDE-EXEC-100-1 (qnfo-ops v2.7.0 endpoint https://qnfo-ops.q08.workers.dev POST /v1/chat/completions, bearer OPS_ROUTER_AUTH_KEY, model QNFO-OPS/ops-exec is the SOLE executor of every code/tool operation — run_code / ops_d1_query / vectorize_query / r2_* / kv_* / workspace_* / email_* / fleet_* / web_* / github_* / issue_* / telemetry_* all run on Cloudflare; the four clients are OpenAI-compatible REST terminals and MUST never execute code locally, never invoke local tools from an ops-exec chat, and never receive a client-executable tool_calls payload; SUPERSEDES the v4.20 hybrid carve-out for source=="deepchat" — the pure server-side loop is now universal and detectSource remains for audit labeling only, strategy never yields hybrid client-handoff for any source; DeepChat / ChatBox / Sanna system prompts embed this block so the client itself forbids local execution; verify per-client probes — from each of the four clients, "run run_code: 12345*6789" MUST return 83810205 with zero client-side execution, and "fleet status" MUST return live /health data — plus ops_ai_log rows carry the correct source per client + all four model keys QNFO-OPS/ops-exec + 7-store prompt parity + prompt-store-verify.py exit 0 + scheduler-guard.py exit 0 + model_guard.py exit 0 after every dual-write (PROMPT-PARITY-1).

## 4. Client configuration matrix

| Client | Config surface | Provider entry | Model | Local-exec posture |
|---|---|---|---|---|
| DeepChat Windows | agent.db app_settings + Roaming app-settings.json (all four keys) | QNFO-OPS · https://qnfo-ops.q08.workers.dev · path /v1 | QNFO-OPS/ops-exec | Remove Code Mode from the ops-chat agent toolchain; embed gate section 3 in the agent system prompt (rule 11 SERVER-SIDE-EXECUTION GUARANTEE stands); no client tool_calls handoff |
| ChatBox Windows | Roaming config.json (xyz.chatboxapp.app) | qnfo-ops · host above · path /v1/chat/completions | ops-exec | Remote OpenAI provider executes nothing locally; keep plugins/artifacts/web-search toggles off for ops chats |
| ChatBox Android | on-device provider entry (per QNFO-OPS-ChatBox-Android-Setup.md 2026-09-03) | same host/path | ops-exec | UA Dart/Flutter/OkHttp -> source=mobile -> pure server loop (verified 2026-09-09 probe okhttp) |
| SannaBot Android | Sanna app custom-endpoint / agent-profile settings | same host/path | ops-exec | Sanna is device-action-first (LLM agent loop that operates the phone) -> DISABLE its action/tool layer for the ops-exec agent or use a tools-off profile; the endpoint never returns tool_calls, so no client-executable payload can arrive |

## 5. Server-side capability inside the loop (what clients may ask the endpoint to run)

fleet_status · ops_issues_list · ops_d1_query (8 D1) · vectorize_query (5 indexes) · r2_* (4 buckets) · kv_get · research_queue / intents_query / candidates_query · backlog_status · service_discover · cf_analytics · telemetry_report / telemetry_analyze · email_check / email_stats / email_mark / email_respond · ops_fleet_log · run_code · web_fetch / web_search · github_repo_read / github_file_write / github_pr · workspace_read / workspace_write / workspace_list / workspace_delete. All server-side on Cloudflare.

## 6. Verification protocol (server-side, same turn)

1. Per client, probe A: "run run_code: compute 12345*6789 and show the result" -> answer text contains 83810205; zero client-side execution attempted.
2. Per client, probe B: "show fleet status" -> live /health data (worker names + versions), not a client-side computation.
3. ops_fleet_log / ops_ai_log: rows for each request carry the expected source (deepchat / chatbox / mobile / other) and finish=stop; no finish_reason=tool_calls handed to a client that cannot execute.
4. Registry: service_discover returns qnfo-ops v2.7.0 with models ops-exec + deepseek-v4-flash.
5. Host-side after any prompt-store write (device-bound, run by the host agent): prompt-store-verify.py exit 0 + scheduler-guard.py exit 0 + model_guard.py exit 0 + all four model keys QNFO-OPS/ops-exec.

## 7. Boundaries & failure modes (adversarial)

- This endpoint cannot write the Windows/Android host stores or run the host guard scripts. Applying the gate = host-agent dual-write to the 7 prompt stores + repo commit + wrangler deploy from the canonical dir + real-client probes. This document is the instruction set; it is NOT proof of application.
- The worker behavior change (hybrid removal, universal pure loop) requires a code change in the qnfo-ops repo + deploy + model check + one real chat per client. Curl-only verification does not exercise real clients (v4.15 rule).
- SannaBot identity unverified. Web search surfaces "Sanna" (github.com/sannabotdev/sannabotapp), an open-source voice-first Android assistant whose design is an on-device LLM agent loop that controls the phone — structurally in tension with 100% server-side. If that is the client, its action layer MUST be off for ops-exec chats (or Sanna excluded from ops chats). If the user's SannaBot is a different app, this row is generic guidance pending a device probe.
- Removing the DeepChat hybrid carve-out may regress flows where DeepChat natively executed tools. Monitor ops_ai_log for a rise in provider_error or changed finish reasons after deploy.
- Falsifier: any ops-exec chat answered via client-side execution, or any ops_ai_log row with finish_reason=tool_calls to a non-executing client, disproves the gate.
- Cost/trust note: server-side execution centralizes compute under the OPS_ROUTER_AUTH_KEY secret; key rotation must update all four clients the same cycle.
