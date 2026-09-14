# Changelog

All notable changes to CDR are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and commits follow
[Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

## [0.1.0] - 2026-09-13

### Added

- Control room dashboard (Next.js 16): runs overview, run detail with execution timeline,
  before/after telemetry charts, root cause finding, diagnosis, generated diff and verification.
- Python runner with the four-phase CDR pipeline: chaos capture, classification,
  repository-aware diagnosis, patch generation and resilience verification.
- Deterministic mock mode that exercises the full pipeline without Docker, k6 or Toxiproxy.
- IBM watsonx.ai (Granite) integration for repository-aware diagnosis with rule-based fallback.
- Supabase sink for run, phase, telemetry, finding, diagnosis, patch and verification data.
- Staging chaos lab: Online Boutique subset (Docker Compose), k6 checkout load, Toxiproxy
  payment-service proxy.
- Postgres schema with RLS policies and realtime publication for runs.
- CI: dashboard lint/build and runner lint/tests.
- Documentation: architecture, deployment, metrics, Bob usage, judging map and demo script.
