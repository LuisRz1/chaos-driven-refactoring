# CDR Runner

Orchestrates the Chaos-Driven Refactoring pipeline:

1. **Chaos injection + collapse capture** — load and fault injection against a real target repo in staging.
2. **Root cause classification** — telemetry and logs mapped to a failure category with evidence.
3. **Repository-aware diagnosis** — watsonx.ai (IBM Granite) analysis with full repository context.
4. **PR generation + resilience verification** — patch generated and verified by re-running the exact same scenario.

## Quickstart

```bash
cd runner
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -e ".[dev]"

python -m cdr doctor
python -m cdr list-scenarios
python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode mock --sink all
```

Mock mode simulates telemetry deterministically so the full pipeline, report generation and
dashboard sync can run without Docker, k6 or Toxiproxy. Live mode uses the same code paths and
is wired to the infrastructure in `infra/`.

## Configuration

Copy `.env.example` from the repository root and export the variables you need:

| Variable | Purpose |
| --- | --- |
| `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` | enable IBM Granite diagnosis |
| `WATSONX_MODEL_ID` | model id, defaults to `ibm/granite-3-8b-instruct` |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | sync runs to the control room |
| `CDR_GITHUB_REPO` | target repository for generated PRs |

Only models allowed by the hackathon scope are accepted (see `cdr/config.py`).

## Tests

```bash
ruff check .
pytest
```
