# Project Overview

## The problem

Resilience today is handled in three silos that never talk to each other:

1. **Chaos engineering** (Gremlin, Chaos Mesh) breaks the system but only diagnoses — a human
   interprets and rewrites code manually.
2. **Observability / APM** (Datadog, Dynatrace, New Relic) finds the root cause in logs and
   metrics but never touches the code; its only automated lever is scaling infrastructure
   (more expensive, fixes nothing).
3. **AI coding agents** (Devin, Copilot Workspace) write code but are reactive to human prompts
   and disconnected from live telemetry.

Nobody closes the loop: **physical collapse → root cause → architecture rewrite → verification**.

## The product

CDR closes that loop with four phases (see [[Pipeline]]):

1. Inject chaos + capture the collapse (k6 load, Toxiproxy faults).
2. Classify the failure: concurrency, memory leak, unresilient dependency, DB saturation.
3. Repository-aware diagnosis and repair — **IBM Bob Shell** reads the actual cloned repo,
   identifies where the failure class originates and applies the minimal fix.
4. Verify: re-run the same chaos scenario against the patched code and report before/after.

Output: a run record with telemetry, root cause evidence, the real `git diff`, Bob task id and
Bobcoins spent, and a stability verdict — all visible in [[Dashboard]].

## Origin story (the pivot)

The team originally designed "FlakyGuard", a flaky-test detector/repairer. Before the hackathon
they pivoted to **Chaos-Driven Refactoring**: same testing/application-maintenance spirit, but
focused on operational resilience — finding and fixing the code that makes a real system collapse
under stress. The original decision document lives at
`../Contexto_Proyecto_CDR_IBM_Bob2_Hackathon.md`.

## Current status (as of the last development session)

- Dashboard deployed on Vercel with live Supabase data, progress bars and Bob attribution.
- Runner works in mock mode end-to-end and can process repos queued from the dashboard UI.
- Bob integration is live: real repository reads, real edits, real `git diff`, Bobcoins tracked
  (`diagnoses.bobcoins`, `patches.bobcoins`).
- Live chaos lab (`infra/`) is ready; verified end-to-end flow is mock mode plus the recorded
  live lab configuration (see [[Roadmap]]).
- 27 runner tests + ruff, dashboard lint/build, CI green.

## Where things live

See the table in [`AGENTS.md`](../AGENTS.md) and [[Architecture]] for the component map.
