# AGENTS.md — CDR (Chaos-Driven Refactoring)

Agent guide for this repository. Read this before changing code. The full knowledge base lives
in [`obsidian-vault/Home.md`](obsidian-vault/Home.md).

## What this project is

CDR closes the APM-to-code gap: it injects chaos and load into a real repository running in
staging, captures the physical collapse, classifies the root cause, has **IBM Bob** read the
actual code and apply a resilience refactor, and verifies the fix by re-running the exact same
scape scenario. Built for the **IBM Bob 2.0 Hackathon** (lablab.ai, Sep 25–27 2026).

Production:

- Dashboard: https://chaos-driven-refactoring.vercel.app
- Repository: https://github.com/LuisRz1/chaos-driven-refactoring
- Supabase project ref: `fepfoabnjldabzghvpvv` (isolated schema `cdr`)

## Repository layout

| Path | Contents |
| --- | --- |
| `dashboard/` | Next.js 16 control room (App Router, Tailwind 4, Recharts), `/api/runs` route, Supabase + mock fallback |
| `runner/` | Python 3.9+ pipeline: queue worker, chaos simulation/live hooks, classifier, Bob repair, verifier, sinks |
| `infra/` | Online Boutique subset (Docker Compose), k6 load scenario, Toxiproxy fault injection |
| `supabase/migrations/` | Postgres schema (schema `cdr`) with RLS, grants, realtime publication |
| `scripts/bob-task.ps1` | Headless IBM Bob Shell task runner with evidence capture |
| `bob_sessions/` | Hackathon evidence: Bob IDE exports/screenshots + headless session JSON |
| `docs/` | Architecture, deployment, metrics, Bob usage, judging map, demo script |
| `obsidian-vault/` | Linked knowledge base ("brain") with the full project context |

## Commands

### Dashboard (Node 24)

```powershell
cd dashboard
npm install          # NOTE: npm ci is broken with npm 11 (@emnapi lockfile bug)
npm run lint
npm run build
npm run dev          # http://localhost:3000
```

### Runner (Python)

```powershell
cd runner
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\ruff check .
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m cdr doctor
.\.venv\Scripts\python -m cdr run --scenario scenarios\checkout-latency-cascade.yaml --mode mock --sink all
.\.venv\Scripts\python -m cdr watch --once     # process one queued analysis
.\.venv\Scripts\python -m cdr watch --pace 6   # continuous worker, 6s per phase for demos
```

### Infra (live chaos lab, requires Docker Desktop)

```powershell
docker compose -f infra\target\docker-compose.yml up -d
k6 run -e BASE_URL=http://localhost:8080 infra\load\checkout-load.js
```

### Deploy

```powershell
cd dashboard
vercel deploy --prod -y
```

## Verification (required before committing)

1. `runner`: `ruff check .` and `pytest` (27 tests) — from `runner/` with the venv.
2. `dashboard`: `npx tsc --noEmit`, `npm run lint`, `npm run build` — from `dashboard/`.
3. CI mirrors both jobs in `.github/workflows/ci.yml`; main must stay green.

**Tests must never call external analyzers.** `runner/tests/conftest.py` forces
`CDR_ANALYZER=rules`, `CDR_CLONE_REPOS=0`, `CDR_BOB_PATCHES=0` and removes credentials. Keep it
that way, otherwise a local `~/.cdr/bob-api-key.txt` will make tests spend real Bobcoins.

## Conventions

- Documentation, commit messages and code identifiers in **English**. Conventional Commits
  (`feat(runner): ...`, `fix(dashboard): ...`, `docs: ...`).
- **No comments in code** unless strictly required.
- Python must stay **3.9 compatible** (no `match`, no runtime `X | Y` unions); ruff
  `line-length = 120`.
- **Never commit secrets.** `BOB_API_KEY`, `WATSONX_*`, `SUPABASE_SERVICE_ROLE_KEY` and
  `GITHUB_TOKEN` live only in environment variables or `~/.cdr/bob-api-key.txt`. IBM scans
  submission repositories and deactivates accounts that leak credentials.
- Generated/local-only artifacts stay gitignored: `.venv/`, `node_modules/`, `.next/`,
  `artifacts/`, `.env*`, `.vercel/`.

## Architecture summary

Two planes:

- **Control plane** (Vercel + Supabase): dashboard, `/api/runs` (service-role insert of a
  `queued` run), run history, progress UI with 5s auto-refresh.
- **Data plane** (local worker): `cdr watch` claims the oldest queued run, executes the 4-phase
  pipeline and streams progress back to Supabase (`runs.status` + `run_phases`).

Pipeline phases: `chaos` (telemetry/live capture) → `classification` (rules → category +
evidence) → `diagnosis` (Bob reads the repo) → `verification` (re-run scenario, before/after
metrics). Status transitions: `queued → running → collapsed → diagnosing → patching → verifying
→ completed|failed`.

Analyzer precedence (`CDR_ANALYZER=auto`):

1. **IBM Bob Shell** (`BOB_API_KEY` present): one **agent** session on a shallow clone of the
   submitted repo — Bob reads the code, applies the minimal fix, and the patch is the real
   `git diff` (files validated against the clone). Bobcoins and task id stored per run.
2. **watsonx.ai Granite** (if configured) — plan-style analysis, template patch.
3. **Deterministic rules** — offline fallback, template patch.

Full details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), vault
[`Architecture.md`](obsidian-vault/Architecture.md).

## Environment variables

| Variable | Where | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_SCHEMA` | Vercel (production+preview) | schema `cdr` |
| `SUPABASE_SERVICE_ROLE_KEY` | Vercel (server route) + runner | — |
| `BOB_API_KEY` | runner (or `~/.cdr/bob-api-key.txt`) | — |
| `CDR_ANALYZER` | runner | `auto` |
| `CDR_BOB_MAX_COST`, `CDR_BOB_PATCH_MAX_COST` | runner | `2`, `2` Bobcoins |
| `CDR_BOB_TIMEOUT_S` | runner | `420` |
| `CDR_CLONE_REPOS`, `CDR_BOB_PATCHES` | runner | `1`, `1` |
| `WATSONX_*` | runner (optional) | Granite `ibm/granite-3-8b-instruct` |

## Bob workflow (hackathon)

- Headless tasks: `powershell -ExecutionPolicy Bypass -File scripts\bob-task.ps1 -Name "task" -MaxCost 2 -Prompt "..."`.
  Evidence (task id, duration, `session_costs`, tool calls, final message) lands in
  `bob_sessions/bobshell-<task>-<timestamp>.json`.
- Bob IDE sessions: export task history markdown + screenshot of the consumption summary into
  `bob_sessions/` (see `bob_sessions/README.md`).
- Budget: 50 Bobcoins total. Track spend in the session JSONs and the Bob portal.
- Bob runtime rules: `--trust --accept-license --format json`, always `--max-cost`; prompt must
  forbid plan files, tests and builds (the repair prompt in `runner/cdr/repair.py` is the
  reference).

## Gotchas

- `npm ci` fails on this repo (npm 11 `@emnapi` lockfile bug) — use `npm install`. Vercel also
  uses `npm install` by default.
- Windows subprocesses: always force `encoding="utf-8", errors="replace"` when capturing
  Bob/git output, otherwise the reader thread crashes with `IndexError` on non-cp1252 bytes.
- PowerShell interpolation pitfall: `".../$var?select=..."` parses `$var?select` as a variable
  name. Use `${var}` in REST URLs.
- After DDL on Supabase, PostgREST may return transient 400/404 until its schema cache reloads.
  For admin REST calls prefer Python `httpx` over PowerShell (PowerShell sometimes fails auth).
- The worker processes the **oldest** queued run first; use `--once` in scripts and the
  continuous loop for the event.
- Bob agent sessions sometimes produce no edits (empty diff). The pipeline then falls back to
  the template patch with `patches.source = "template"`; runs never fail because of that.
- The finding file path only becomes repo-real when Bob identifies/changes files; otherwise it
  keeps the scenario template path.
- Mock mode telemetry is deterministic simulation — the real chaos lab is `infra/` (live mode).

## Pointers

- Knowledge base: [`obsidian-vault/Home.md`](obsidian-vault/Home.md)
- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · Deployment:
  [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) · Metrics: [`docs/METRICS.md`](docs/METRICS.md)
- Bob usage: [`docs/BOB_USAGE.md`](docs/BOB_USAGE.md) · Judging map:
  [`docs/JUDGING_MAP.md`](docs/JUDGING_MAP.md) · Demo script:
  [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
