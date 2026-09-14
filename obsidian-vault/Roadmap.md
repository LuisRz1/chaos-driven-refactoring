# Roadmap

## Done

- [x] Four-phase pipeline with deterministic mock mode and live-lab hooks.
- [x] Supabase schema `cdr` with RLS, realtime, service-role writes.
- [x] Dashboard: overview, submission form, run detail, before/after charts, diff viewer,
      progress bars, 5s auto-refresh.
- [x] Queue worker (`cdr watch`) with atomic claim, per-phase progress streaming and `--pace`.
- [x] **IBM Bob runtime repair**: agent session on the real clone, real `git diff`, Bobcoins and
      task id tracked per diagnosis and patch.
- [x] Bob Shell headless task runner with evidence capture (`scripts/bob-task.ps1`).
- [x] Vercel + Supabase production deployment wired end to end.
- [x] CI (dashboard lint/build + runner ruff/pytest), 27 runner tests.
- [x] Docs (AGENTS.md, docs/, this vault).

## Next (hackathon priorities)

- [ ] **Live mode hardening**: drive the real `infra/` lab from the pipeline (compose control,
      k6 invocation, Toxiproxy toxics) instead of the mock simulation; record one full live run
      for the demo video.
- [ ] **Concurrency bisection integration**: wire `runner/cdr/bisector.py` into the concurrency
      branch of the classifier so the differentiated path is visible in the UI.
- [ ] **PR automation**: enable `--create-pr` end to end (clone, apply diff, push branch, open
      PR) and surface the PR URL on the patch panel.
- [ ] **Bob prompt profiles per category**: craft repair prompts that produce deeper fixes
      (circuit breaker, pooling) instead of broad edits.
- [ ] **Vault/evidence polish** before submission: IDE session exports + screenshots, final
      `bob_sessions` index update.
- [ ] Slide deck + 3-minute video per `docs/DEMO_SCRIPT.md`.

## Later

- [ ] Deploy the worker to IBM Cloud Code Engine with secrets (uses the $80 credits).
- [ ] Realtime subscriptions in the dashboard (publication already enabled) instead of polling.
- [ ] Multi-user auth/workspaces in the dashboard and per-team run isolation.
- [ ] SLO dashboards and historical trends per repository.
- [ ] Verification against multiple chaos scenarios per run (regression matrix).
- [ ] Cost accounting: aggregate Bobcoins/Bob usage per project.

## Open questions

- How strict is lablab about Bob IDE exports vs Bob Shell sessions? (Current plan: provide both.)
- Should submitted repositories be limited to public GitHub repos? (Current clone uses HTTPS
  without auth, so yes.)
- How many Bobcoins can the runtime spend during judging without exhausting the trial?
