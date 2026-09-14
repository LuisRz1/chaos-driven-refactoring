# Runner

Python package `runner/cdr` (editable install as `cdr-runner`). Python 3.9 compatible.

## CLI

```powershell
python -m cdr doctor                                        # effective config, no secrets
python -m cdr list-scenarios [--dir runner/scenarios]
python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode mock --sink all
python -m cdr run ... --create-pr                           # attempt a real PR (needs clone + gh)
python -m cdr watch [--interval 5] [--once] [--pace 6] [--mode mock|live]
```

`watch` is the queue worker: claims the oldest queued run from Supabase, runs the pipeline and
updates the same run row. `--pace N` sleeps N seconds after each phase — useful so a live demo
audience can watch the progress bar move. `--once` processes a single run (use it in scripts).

## Modules

| File | Responsibility |
| --- | --- |
| `cli.py` | argparse entrypoints: `run`, `watch`, `list-scenarios`, `doctor` |
| `queue.py` | Supabase queue: atomic claim, `scenario_for`, `mark_failed` |
| `pipeline.py` | 4-phase orchestration, progress callbacks, summary assembly |
| `telemetry.py` | deterministic mock telemetry simulation + collapse detection |
| `classifier.py` | signal-to-category rules with evidence |
| `repair.py` | **BobRepairer**: single Bob agent session → real git diff + diagnosis |
| `diagnoser.py` | plan-mode Bob / watsonx / rules analysis; free-form parsing helpers |
| `bob_client.py` | Bob Shell subprocess wrapper (`bob run`), JSON result parsing |
| `repo_context.py` | shallow clone/checkout of the submitted repository |
| `workspace.py` | git helpers for managed clones: reset, stage, diff, file lists |
| `patcher.py` | template patches + optional PR creation |
| `verifier.py` | before/after comparison and stability verdict |
| `progress.py` | per-phase Supabase publishing (`run_phases`, status, partial data) |
| `sinks.py` | stdout / JSON artifacts / Supabase writers (`emit`, `emit_update`) |
| `models.py` | dataclasses for scenario, telemetry, finding, diagnosis, patch, verification |
| `config.py` | environment-driven `Settings` + blocked watsonx models |
| `watsonx.py` | IAM token + text generation REST client |

## Mock vs live

- **Mock** (`--mode mock`, default): deterministic telemetry simulation. Whole pipeline,
  artifacts and Supabase sync work without Docker, k6 or Toxiproxy. Used by CI and demos.
- **Live** (`--mode live`): executes against the `infra/` chaos lab. `infra/README.md` documents
  the compose stack, k6 scenario and Toxiproxy toxic commands.

## Tests

`runner/tests` — 27 tests covering scenario loading, telemetry, classification, verification,
pipeline progress callbacks, patcher templates, Bob output parsing and diagnoser fallbacks.

> [!warning] Tests must stay offline.
> `conftest.py` forces `CDR_ANALYZER=rules`, `CDR_CLONE_REPOS=0`, `CDR_BOB_PATCHES=0` and
> removes credentials. Without it, a local `~/.cdr/bob-api-key.txt` would make tests spend real
> Bobcoins and clone repositories.

## Environment

See the table in [`AGENTS.md`](../AGENTS.md#environment-variables) and [[Deployment]].
`python -m cdr doctor` prints the effective configuration without secrets.
