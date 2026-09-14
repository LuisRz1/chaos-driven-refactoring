# Pipeline

`runner/cdr/pipeline.py` orchestrates four phases. Each phase publishes progress to Supabase so
the dashboard can show where the run is (see [[Dashboard]]).

## Phase 1 — Chaos + collapse capture (`chaos`)

- Module: `runner/cdr/telemetry.py` (mock) + `infra/` (live).
- Produces: telemetry samples (p95, p99, error rate, rps), peak metrics, `time_to_collapse_s`
  and log signals.
- Status after phase: `collapsed` (if a collapse was detected) or `running`.
- Publishes the "before" telemetry series immediately.

## Phase 2 — Root cause classification (`classification`)

- Module: `runner/cdr/classifier.py`.
- Maps log signals to a category with confidence and evidence:
  `concurrency`, `memory_leak`, `unresilient_dependency`, `db_saturation`, `unknown`.
- Status: `diagnosing`.

## Phase 3 — Repository-aware diagnosis and repair (`diagnosis`)

- Primary path (`BobRepairer`, `runner/cdr/repair.py`): one Bob agent session on the cloned
  submitted repo. Bob reads the code, applies the minimal fix and reports analysis + files.
  The patch is the real `git diff`; `target_files` are the actually changed files.
- Fallbacks: plan-mode analysis (`diagnoser.py`) with watsonx Granite or deterministic rules,
  plus a template patch from `patcher.py` when Bob is unavailable or produced no edits.
- Side effect: `finding.file_path` is updated to a real repository path when Bob identifies one.
- Status: `patching` → `verifying`.

## Phase 4 — Verification (`verification`)

- Module: `runner/cdr/verifier.py`.
- Re-runs the identical scenario against the patched code (mock simulation or live lab),
  computes improvement percentages for p95, p99, error rate and collapse elimination, and
  decides `stable`.
- Status: `completed` (stable) or `failed`.

## Status transitions

```text
queued → running → collapsed → diagnosing → patching → verifying → completed | failed
```

Progress events per phase: `run_phases` rows (labelled, with detail), replacing the previous
row for the same phase on retries. `SupabaseProgress` in `runner/cdr/progress.py` owns this.

## Run result

`RunResult` (in `runner/cdr/models.py`) contains telemetry before/after, phases, finding,
diagnosis (with `bob_task_id`, `bobcoins`, `target_files`), patch (with `source`,
`bob_task_id`, `bobcoins`) and verification. `sinks.py` writes it to stdout, JSON artifacts and
Supabase; the worker uses `emit_update` for claimed runs.

## Scenario files

YAML in `runner/scenarios/`:

```yaml
name: checkout-latency-cascade
target: GoogleCloudPlatform/microservices-demo
commit: b9c7d2f
mode: live
load: { tool: k6, endpoint: ..., vus: 200, duration_s: 120, injection_at_s: 30 }
chaos: { tool: toxiproxy, proxy: payment-service, fault: latency, attributes: { latency_ms: 800 } }
thresholds: { p95_ms: 500, error_rate: 0.05, collapse_error_rate: 0.25 }
```

`SupabaseQueue.scenario_for(row)` loads the YAML by name and overrides target/commit/mode with
the values submitted from the dashboard.
