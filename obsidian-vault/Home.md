# CDR Brain — Home

Knowledge base for **CDR (Chaos-Driven Refactoring)**, built for the IBM Bob 2.0 Hackathon.
Open this folder as an Obsidian vault. Everything an agent or teammate needs is linked below.

> [!info] One-liner
> CDR injects chaos into a real repository, captures the physical collapse, has **IBM Bob**
> read the code and apply a resilience refactor, and verifies the fix by re-running the same
> scenario. It closes the APM-to-code gap.

## Start here

- [[Project Overview]] — what CDR is, the problem, the pivot story, current status
- [[Architecture]] — control plane vs data plane, analyzer precedence, tech stack
- [[Pipeline]] — the four phases, status transitions, progress streaming
- [[Runbook]] — copy-paste commands for dev, demo, deploy, maintenance
- [[Known Issues and Gotchas]] — read before debugging anything

## Components

- [[Runner]] — Python pipeline, queue worker, Bob repair session, verifier
- [[Dashboard]] — Next.js control room, `/api/runs`, progress UI
- [[Database and Supabase]] — schema `cdr`, RLS, realtime, admin operations
- [[Deployment]] — Vercel + Supabase + worker, CI, security checklist
- [[IBM Bob Integration]] — how Bob analyzes and patches; evidence and budget

## Product and hackathon

- [[Hackathon Context]] — event facts, judging criteria, submission checklist
- [[Metrics and Business Value]] — p95/p99, collapse, downtime economics
- [[Research and Positioning]] — competitive landscape, academic references
- [[Evidence]] — `bob_sessions/` conventions and headless session log
- [[Roadmap]] — what is done, what is next
- [[Glossary]] — vocabulary for fast onboarding

## External references

- Repository: https://github.com/LuisRz1/chaos-driven-refactoring
- Dashboard (production): https://chaos-driven-refactoring.vercel.app
- Agent guide in the repo: [`AGENTS.md`](../AGENTS.md)
- Original context document: `../Contexto_Proyecto_CDR_IBM_Bob2_Hackathon.md` (workspace root,
  outside the repo)
