# Known Issues and Gotchas

Read this before debugging. Everything here has burned someone once.

## Tooling

- **`npm ci` is broken** with the committed lockfile on npm 11 (`@emnapi` optional-dependency
  bug). Use `npm install` locally, in CI and on Vercel.
- **Windows subprocess decoding**: Bob and git output must be captured with
  `encoding="utf-8", errors="replace"`. Without it, a non-cp1252 character kills the reader
  thread and you get a misleading `IndexError: list index out of range`.
- **PowerShell interpolation**: `".../$var?select=..."` parses `$var?select` as a variable
  name. Use `${var}` in REST URLs. For admin writes prefer Python `httpx` over
  `Invoke-RestMethod` (PowerShell occasionally fails auth on DELETE/POST).
- **PostgREST schema cache**: right after DDL, requests may return transient `400`/`404` until
  the cache reloads. Retry; there is no data problem.
- **Vercel CLI** deploys from `dashboard/`; use `vercel deploy --prod -y`. Git integration is
  not configured.

## Runner

- The worker claims the **oldest** queued run. In scripts use `--once`; for the event use the
  continuous loop.
- `BOB_API_KEY` can come from the environment or `~/.cdr/bob-api-key.txt`. Tests are isolated
  via `conftest.py`; do not remove that isolation or CI/local test runs will spend Bobcoins.
- Bob agent sessions sometimes finish with **no edits** → `repair()` returns `None` and the
  pipeline falls back to the template patch (`patches.source = "template"`). Runs never fail
  for this reason.
- When Bob does edit, the prompt limits it to ~3 files, but it can still choose a broad or
  generic fix (e.g. adding `from __future__ import annotations`). Prompt quality matters.
- The finding `file_path` only becomes repository-real when Bob changes files; otherwise it
  reflects the scenario template (e.g. `src/checkoutservice/main.go`) which may not exist in the
  submitted repo.
- Mock telemetry is deterministic (same numbers every run) — expected, it is a simulation.
- Clones live in `artifacts/repos/`; `git reset --hard` + `git clean -fd` run there before each
  Bob session. Never point the workspace helpers at other directories
  (`is_managed_workspace` guards this).
- Bob repairs run with `--max-cost`; if the cap is hit mid-session the diff can be broader than
  intended, and analysis parsing may fall back to derived text.

## Dashboard

- Without Supabase env vars the UI silently renders deterministic mock data — useful for
  demos, confusing when debugging data issues. Check env vars first.
- Queued runs with an empty `summary` used to crash the server component; formatters now handle
  `undefined` (keep it that way) and `src/app/error.tsx` provides a friendly boundary.
- Auto-refresh runs every 5 seconds for active runs; a completed run appears a few seconds after
  the worker finishes.
- `/api/runs` needs `SUPABASE_SERVICE_ROLE_KEY` on Vercel; without it the API returns 503.

## Data

- CDR tables live in schema `cdr`; forgetting `Accept-Profile`/`Content-Profile` headers in raw
  REST calls yields `PGRST` errors about a missing table.
- Deleting a run cascades to phases, samples, findings, diagnoses, patches and verifications.
- The Supabase project is shared with other applications; never touch `public` or other schemas.
