# Deployment

## Current production setup

| Component | Platform | Notes |
| --- | --- | --- |
| Dashboard | Vercel project `chaos-driven-refactoring` | Root directory `dashboard/`, deployed from CLI |
| Database / realtime / storage | Supabase `fepfoabnjldabzghvpvv`, schema `cdr` | shared project, isolated schema |
| Runner | Local Windows machine (Docker Desktop for live mode) | processes queued analyses |
| AI | IBM Bob Shell (default), watsonx Granite (optional) | Bobcoins tracked per run |

Dashboard: https://chaos-driven-refactoring.vercel.app

## Dashboard (Vercel)

```powershell
cd dashboard
vercel link --yes --project chaos-driven-refactoring   # first time
vercel env add NEXT_PUBLIC_SUPABASE_URL production --value "https://fepfoabnjldabzghvpvv.supabase.co"
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production --value "<anon-jwt>"
vercel env add NEXT_PUBLIC_SUPABASE_SCHEMA production --value "cdr"
vercel env add SUPABASE_SERVICE_ROLE_KEY production --value "<service-role>" --sensitive
vercel deploy --prod -y
```

Repeat the env adds for the `preview` target when needed. `vercel link` writes
`dashboard/.env.local` (gitignored).

## Supabase

1. Create the project (or reuse a shared one) and run `supabase/migrations/0001_init.sql`.
2. Expose the schema: project settings → API → Exposed schemas, add `cdr` (API equivalent:
   `PATCH /v1/projects/{ref}/postgrest` with `db_schema`).
3. Collect the URL, `anon` key (dashboard) and `service_role` key (runner + API route only).

## Runner (local)

```powershell
cd runner
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"

$env:SUPABASE_URL = "https://fepfoabnjldabzghvpvv.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "<service-role>"
$env:SUPABASE_SCHEMA = "cdr"
$env:BOB_API_KEY = (Get-Content "$env:USERPROFILE\.cdr\bob-api-key.txt" -Raw).Trim()

.\.venv\Scripts\python.exe -m cdr watch          # continuous worker
.\.venv\Scripts\python.exe -m cdr watch --once   # single run
```

Live chaos mode additionally needs Docker Desktop and the `infra/` stack (see [[Runbook]]).

## CI/CD

- GitHub Actions (`.github/workflows/ci.yml`): dashboard `npm install` + lint + build; runner
  `pip install -e ".[dev]"` + ruff + pytest. Both must stay green on `main`.
- Vercel deploys are CLI-driven (`vercel deploy --prod -y`). Git integration is optional and not
  configured; if enabled, set the project root directory to `dashboard`.
- Watch out: `npm ci` is broken on npm 11 with this lockfile (`@emnapi` bug) — CI and local use
  `npm install`.

## IBM Cloud Code Engine (stretch)

The runner is container-ready: slim Python image, `pip install -e .`, run `python -m cdr watch`.
Store watsonx/Bob/Supabase credentials as Code Engine secrets. Not implemented yet
(see [[Roadmap]]).

## Security checklist

- Never commit `.env`, API keys or the database password; IBM scans submission repositories and
  deactivates accounts that leak Bob or IBM Cloud credentials.
- Rotate the Supabase personal access token and the Bob API key after the hackathon.
- Out-of-scope watsonx models are blocked in `runner/cdr/config.py`.
- Generated PRs are opt-in (`--create-pr`).
