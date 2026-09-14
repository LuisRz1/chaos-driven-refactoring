# Dashboard

Next.js 16 App Router app in `dashboard/` (TypeScript, Tailwind CSS 4, Recharts). Deployed on
Vercel at https://chaos-driven-refactoring.vercel.app.

## Pages

- **`/` — Overview**: hero, "Analyze a repository" form, KPI cards (runs tracked, collapses,
  avg p95 reduction, avg AI diagnosis), 4-step pipeline strip and the experiment run cards with
  live progress bars.
- **`/runs/[id]` — Run detail**: KPI row (time to collapse, p95 before→after, error rate,
  diagnosis time), before/after charts with a chaos-injection reference line, execution timeline,
  root cause finding, resilience verification panel, repository-aware diagnosis
  (with `bob_task_id` and Bobcoins attribution and "Identified locations") and the generated
  patch with diff viewer and generation attribution.

## Data layer

`src/lib/data.ts`:

1. If `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` are configured, it queries
   Supabase using `client.schema(supabaseSchema)` (schema `cdr`, env
   `NEXT_PUBLIC_SUPABASE_SCHEMA`, default `cdr`).
2. Otherwise it falls back to deterministic demo data in `src/lib/mock-data.ts`, so the UI is
   always demoable.

The run detail page merges: run row, `run_phases`, `telemetry_samples` (kind `before`/`after`),
`findings`, `diagnoses`, `patches`, `verifications`.

## Submission flow

`src/components/analyze-form.tsx` posts `{repoUrl, commit, scenario, mode}` to `/api/runs`
(`src/app/api/runs/route.ts`), which:

- validates the GitHub URL / `owner/repo` format and the allowed scenarios;
- inserts a `queued` run with a generated `run-xxxxxxxx` id using the service role key
  (server-side only);
- returns the run id; the form then refreshes the page.

The **worker** (`cdr watch`) picks it up (see [[Runner]] and [[Pipeline]]).

## Progress UX

- `src/lib/progress.ts` maps run status and phases to `{percent, label}`.
- Active runs render a cyan progress bar; queued runs show "the worker will start it
  automatically".
- `AutoRefresh` triggers `router.refresh()` every 5 seconds while active runs exist.

## Commands

```powershell
cd dashboard
npm install        # npm ci is broken on npm 11 (@emnapi); use install
npm run lint
npm run build
npm run dev
vercel deploy --prod -y
```

## Environment variables (Vercel)

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | public read key (RLS-protected) |
| `NEXT_PUBLIC_SUPABASE_SCHEMA` | `cdr` |
| `SUPABASE_SERVICE_ROLE_KEY` | server-only insert in `/api/runs` (sensitive) |

`vercel link` creates `dashboard/.env.local` (gitignored).
