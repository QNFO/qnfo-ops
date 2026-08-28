# QNFO Cloud Scheduler (qnfo-cloud-ops)

Cloud replacement for the local DeepChat scheduled-task fleet.

- `worker.js` — single Worker hosting 11 cron jobs (see AMS_SCHEDULE table in source)
- `metadata.json` — deploy metadata (bindings; deploy via Workers API PUT multipart with `files` field)
- Cron triggers are managed via the schedules API and self-adjust for DST (weekly-ops job).
- Secrets: INFRA_TOKEN, EMAIL_API_KEY, DIGEST_TO, GH_TOKEN, GMAIL_PASS, CF_TOKEN, OPS_ADMIN_TOKEN.
- Docs: scheduler_migration table in qnfo-audit tracks per-job migration status.
