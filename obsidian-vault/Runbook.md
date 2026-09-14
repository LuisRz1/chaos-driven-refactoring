# Runbook

Copy-paste recipes. Working directory is the repository root unless stated otherwise.

## Local development

```powershell
# Dashboard
cd dashboard; npm install; npm run dev            # http://localhost:3000

# Runner checks
cd runner
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m cdr doctor
```

## Run a scenario directly (no queue)

```powershell
cd runner
.\.venv\Scripts\python.exe -m cdr run --scenario scenarios\checkout-latency-cascade.yaml --mode mock --sink all
# artifacts land in ..\artifacts\<run-id>\run.json + report.md
```

## Queue demo (dashboard → worker)

1. Open https://chaos-driven-refactoring.vercel.app and submit a repo in "Analyze a repository".
2. Start the worker with credentials exported:

```powershell
cd runner
$env:SUPABASE_URL = "https://fepfoabnjldabzghvpvv.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "<service-role>"
$env:SUPABASE_SCHEMA = "cdr"
$env:BOB_API_KEY = (Get-Content "$env:USERPROFILE\.cdr\bob-api-key.txt" -Raw).Trim()
.\.venv\Scripts\python.exe -m cdr watch --pace 6
```

The dashboard updates every 5 seconds; the detail page shows the phase timeline and progress.

## Live chaos lab

```powershell
docker compose -f infra\target\docker-compose.yml up -d
# inject latency
curl -s -X POST http://localhost:8474/proxies/payment-service/toxics -H "Content-Type: application/json" -d '{"name":"latency","type":"latency","attributes":{"latency":800,"jitter":100}}'
k6 run -e BASE_URL=http://localhost:8080 infra\load\checkout-load.js
# remove the fault
curl -s -X DELETE http://localhost:8474/proxies/payment-service/toxics/latency
```

## Deploy the dashboard

```powershell
cd dashboard
vercel deploy --prod -y
```

## Inspect or clean runs (admin REST via Python httpx)

```powershell
.\runner\.venv\Scripts\python.exe -c "import httpx; k='<service-role>'; h={'apikey':k,'Authorization':'Bearer '+k,'Accept-Profile':'cdr','Content-Profile':'cdr'}; [print(r['id'], r['status'], r['target_repo']) for r in httpx.get('https://fepfoabnjldabzghvpvv.supabase.co/rest/v1/runs?select=id,status,target_repo&order=started_at.desc', headers=h, timeout=30).json()]"
# delete a run (children cascade)
.\runner\.venv\Scripts\python.exe -c "import httpx; k='<service-role>'; h={'apikey':k,'Authorization':'Bearer '+k,'Accept-Profile':'cdr','Content-Profile':'cdr'}; print(httpx.delete('https://fepfoabnjldabzghvpvv.supabase.co/rest/v1/runs?id=eq.run-xxxxxxxx', headers=h, timeout=30).status_code)"
```

## Bob headless task with evidence

```powershell
powershell -ExecutionPolicy Bypass -File scripts\bob-task.ps1 -Name "my-task" -MaxCost 2 -Prompt "Work in this repository root. ..."
```

## Maintenance

- Reset a managed clone: delete `artifacts/repos/<owner>-<name>`; the runner re-clones on demand.
- Clear stale artifacts: `Remove-Item artifacts\repo* -Recurse -Force` (never inside `artifacts/repos` while a run is active).
- Rotate secrets after the hackathon: Supabase personal access token, `BOB_API_KEY`, database
  password, Vercel env vars.
