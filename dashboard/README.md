# Dashboard (control room)

Next.js 16 App Router application for exploring CDR runs:

- `/` — KPI overview and experiment runs.
- `/runs/[id]` — execution timeline, before/after telemetry charts, root cause finding,
  repository-aware diagnosis, generated diff and resilience verification.

## Data sources

1. **Supabase** — if `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set, the
   app reads `runs`, `run_phases`, `telemetry_samples`, `findings`, `diagnoses`, `patches` and
   `verifications`.
2. **Deterministic demo data** — when Supabase is not configured, the app falls back to
   `src/lib/mock-data.ts` so the UI stays demoable everywhere.

## Commands

```bash
npm install
npm run dev      # http://localhost:3000
npm run lint
npm run build
```
