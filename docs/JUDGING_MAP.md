# Judging map

How CDR addresses the four lablab.ai judging criteria, and where the evidence lives.

## Application of Technology

| What judges look for | Evidence |
| --- | --- |
| Clear, central application of IBM Bob 2.0 | `docs/BOB_USAGE.md`, `bob_sessions/` (exports + screenshots) |
| Advanced features used for real work | Agent mode for the pipeline, parallel tasks for dashboard/runner, subagents for scoped modules, document understanding for research alignment |
| Technical depth beyond a wrapper | Real chaos engineering (k6 + Toxiproxy), failure taxonomy, repository-aware diagnosis, verification by re-running the same scenario |
| IBM stack | watsonx.ai Granite for diagnosis (`runner/cdr/watsonx.py`), Supabase control plane, Code Engine deployment path |

## Business Value

| What judges look for | Evidence |
| --- | --- |
| High-priority problem | APM-to-code gap: chaos tools diagnose, APM localizes, AI agents code — nobody closes the loop (`README.md`, context doc §2.2) |
| Quantified impact | p95 −95%, p99 −94%, error rate −99%, collapse eliminated, diagnosis 3.2 min vs 95 min manual (`docs/METRICS.md`) |
| Money framing | Downtime > $300k/hour in FinTech/e-commerce; prevented-incident formula in `docs/METRICS.md` |
| Clear target users | CTOs, DevOps leads and SRE teams in FinTech, e-commerce and streaming |

## Originality

| What judges look for | Evidence |
| --- | --- |
| Blue ocean, not a clone | No existing tool combines (a) real telemetry-driven collapse, (b) business-logic rewrite inside the app repo and (c) autonomous verification under re-injected chaos |
| Research-grounded novelty | ChaosEater (ASE 2025) automates chaos but only edits K8s config; AIOpsLab (MLSys 2025) shows mitigation is where agents fail (~55% best case) — CDR attacks mitigation with a verified PR |
| Demo differentiation | Concurrency bisection path with parallel subagents isolating the exact concurrent section |

## Presentation

| What judges look for | Evidence |
| --- | --- |
| Clear story and demo | `docs/DEMO_SCRIPT.md`; dashboard tells the collapse → fix → verified story in one screen flow |
| Working artifact | `dashboard/` (Vercel URL), `runner/` CLI with reproducible mock and live modes |
| Documentation quality | `README.md`, `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/METRICS.md` — all English |
| Submission completeness | Title, short/long description, tags, cover, video, slides, demo URL, repo URL, `bob_sessions/` |
