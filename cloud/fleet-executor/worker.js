// fleet-executor v0.2.0 - dynamic task execution engine
// Reads fleet_tasks from qnfo-audit D1, executes by type, writes fleet_runs ledger.
// v0.2.0: all 9 D1 stores bound (AUDIT/LIVING/PORTFOLIO/OUTREACH/GRAPH/JNL/IPATENT/CMS/PERSONAL) + workflow type.
const VERSION = "fleet-executor/0.2.0";

function json(obj, status) {
  return new Response(JSON.stringify(obj), { status: status || 200, headers: { "content-type": "application/json" } });
}

function dbFor(def, env) {
  const name = (def && def.db) || "AUDIT";
  const b = env[name];
  if (!b) throw new Error("no D1 binding: " + name);
  return b;
}

async function runAI(def, env) {
  const model = def.model || "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
  const resp = await env.AI.run(model, {
    messages: [{ role: "user", content: def.prompt || "ping" }],
    max_tokens: def.max_tokens || 1024
  });
  const text = typeof resp === "string" ? resp : (resp.response || JSON.stringify(resp));
  return { type: "ai", model: model, output: String(text).slice(0, 2000) };
}

async function runSQL(def, env) {
  const db = dbFor(def, env);
  const res = await db.prepare(def.sql).all();
  return { type: "sql", db: def.db || "AUDIT", rows: (res.results || []).length, sample: (res.results || []).slice(0, 3) };
}

async function runHTTP(def) {
  const resp = await fetch(def.url, { method: def.method || "GET", headers: def.headers || {} });
  const text = await resp.text();
  return { type: "http", status: resp.status, body: text.slice(0, 500) };
}

async function executeStep(step, env) {
  if (step.type === "ai") return runAI(step, env);
  if (step.type === "sql") return runSQL(step, env);
  if (step.type === "http") return runHTTP(step);
  throw new Error("unsupported step type: " + step.type);
}

async function executeTask(task, env) {
  let def = {};
  try { def = JSON.parse(task.definition || "{}"); } catch (e) { def = {}; }
  if (task.type === "workflow") {
    const steps = def.steps || [];
    const results = [];
    for (let i = 0; i < steps.length; i++) {
      results.push(await executeStep(steps[i], env));
    }
    return { type: "workflow", steps_run: results.length, results: results };
  }
  def.type = task.type;
  return executeStep(def, env);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") return json({ ok: true, version: VERSION });
    if (url.pathname === "/run" && request.method === "POST") {
      let body = {};
      try { body = await request.json(); } catch (e) { return json({ ok: false, error: "bad json" }, 400); }
      const taskId = body.task_id;
      if (!taskId) return json({ ok: false, error: "missing task_id" }, 400);
      const cronName = body.cron_name || "manual";
      const task = await env.AUDIT.prepare("SELECT * FROM fleet_tasks WHERE id = ?1 AND enabled = 1").bind(taskId).first();
      if (!task) return json({ ok: false, error: "task not found or disabled" }, 404);
      const started = new Date().toISOString();
      const prior = await env.AUDIT.prepare("SELECT id FROM fleet_runs WHERE task_id = ?1 AND cron_name = ?2 ORDER BY id DESC LIMIT 1").bind(taskId, cronName).first();
      const runId = prior ? prior.id : null;
      if (runId) {
        await env.AUDIT.prepare("UPDATE fleet_runs SET status = 'running', started_at = ?1 WHERE id = ?2").bind(started, runId).run();
      }
      try {
        const result = await executeTask(task, env);
        const done = new Date().toISOString();
        const resStr = JSON.stringify(result).slice(0, 4000);
        if (runId) {
          await env.AUDIT.prepare("UPDATE fleet_runs SET status = 'ok', finished_at = ?1, result = ?2 WHERE id = ?3").bind(done, resStr, runId).run();
        } else {
          await env.AUDIT.prepare("INSERT INTO fleet_runs (task_id, cron_name, status, started_at, finished_at, result) VALUES (?1, ?2, 'ok', ?3, ?4, ?5)").bind(taskId, cronName, started, done, resStr).run();
        }
        return json({ ok: true, run_id: runId, result: result });
      } catch (err) {
        const done = new Date().toISOString();
        const msg = String(err && err.message ? err.message : err).slice(0, 1000);
        if (runId) {
          await env.AUDIT.prepare("UPDATE fleet_runs SET status = 'failed', finished_at = ?1, error = ?2 WHERE id = ?3").bind(done, msg, runId).run();
        } else {
          await env.AUDIT.prepare("INSERT INTO fleet_runs (task_id, cron_name, status, started_at, finished_at, error) VALUES (?1, ?2, 'failed', ?3, ?4, ?5)").bind(taskId, cronName, started, done, msg).run();
        }
        return json({ ok: false, error: msg }, 500);
      }
    }
    return json({ ok: false, error: "not found" }, 404);
  }
};
