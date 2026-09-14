# Database and Supabase

## Instance

- Project ref: `fepfoabnjldabzghvpvv` (`supabase-coral-tree`, shared with other applications).
- CDR lives in an **isolated schema `cdr`** inside that project.
- Dashboard URL: `https://fepfoabnjldabzghvpvv.supabase.co`.
- PostgREST exposes `public,graphql_public,cdr` (project setting `db_schema`).
- The database password is stored locally at `C:\Users\edwin\.cdr-supabase-db-password.txt`
  (never in the repository).

## Tables (schema `cdr`)

| Table | Contents |
| --- | --- |
| `projects` | analyzed repositories |
| `scenarios` | chaos scenario catalogue |
| `runs` | one row per experiment: status, mode, target, summary jsonb, collapse flag |
| `run_phases` | per-phase progress rows (chaos, classification, diagnosis, verification) |
| `telemetry_samples` | time series, `kind` = `before` / `after` |
| `findings` | failure category, confidence, root cause, evidence, real file path |
| `diagnoses` | analyzer model, analysis markdown, proposed change, `bob_task_id`, `bobcoins`, `target_files` jsonb |
| `patches` | branch, files_changed, real diff, `source` (`bob-shell` / `template`), `bob_task_id`, `bobcoins` |
| `verifications` | stability verdict, before/after snapshots, improvement percentages |

Indexes on `runs(started_at)`, `run_phases(run_id)`, `telemetry_samples(run_id)`,
`findings(run_id)`. Foreign keys cascade from `runs` onwards.

## Security model

- RLS enabled on every table; public `SELECT` policies for `anon` (demo dashboard).
- Writes come from the runner with the **service role** key (bypasses RLS) using
  `Accept-Profile: cdr` / `Content-Profile: cdr`.
- The `/api/runs` route uses the service role server-side only.
- Realtime publication includes `cdr.runs`, `cdr.run_phases`, `cdr.telemetry_samples` (the UI
  currently polls every 5s; realtime is ready for a future upgrade).

## Migrations

`supabase/migrations/0001_init.sql` creates the schema, tables, indexes, RLS policies, grants
(`anon`/`authenticated` select, `service_role` all) and adds the realtime tables. Apply it to a
fresh project before pointing the app at it.

## Admin operations (from this machine)

DDL is applied through the Management API using the Supabase personal access token:

```powershell
$headers = @{ Authorization = "Bearer $env:SUPABASE_ACCESS_TOKEN"; "Content-Type" = "application/json" }
$body = @{ query = "alter table cdr.diagnoses add column if not exists ..." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://api.supabase.com/v1/projects/fepfoabnjldabzghvpvv/database/query" -Headers $headers -Body $body
```

For data REST calls (insert/update/delete/select as admin) prefer Python `httpx` with
`apikey` + `Authorization` + profile headers — PowerShell occasionally fails auth on writes.

```powershell
.\runner\.venv\Scripts\python.exe -c "import httpx; key='<service-role>'; h={'apikey':key,'Authorization':'Bearer '+key,'Accept-Profile':'cdr','Content-Profile':'cdr'}; print(httpx.get('https://fepfoabnjldabzghvpvv.supabase.co/rest/v1/runs?select=id,status', headers=h, timeout=30).json())"
```

## Gotchas

- After a DDL change PostgREST may return transient `400` / `404` until its schema cache
  reloads; retry after a few seconds.
- Weird `PGRST` errors mentioning a schema usually mean a missing `Accept-Profile` header.
- The runner's `SupabaseSink` and `SupabaseProgress` both send `Prefer: return=minimal` and the
  schema profile headers; keep them in sync when adding tables or columns.
