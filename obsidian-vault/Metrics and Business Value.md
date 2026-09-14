# Metrics and Business Value

All before/after comparisons run under an **identical load profile and fault injection** — the
core methodological claim of CDR. Details in [`docs/METRICS.md`](../docs/METRICS.md).

## Latency

- **p95 / p99** from the load generator, per run window. Before = chaos run that collapses;
  after = identical scenario against the patched code.

## Reliability

- **Error rate** — share of failed requests (5xx, timeouts) over the window.
- **Time to collapse** — seconds until p95 crosses 3× the threshold or error rate crosses the
  collapse threshold. `null` after the fix means no collapse was reproduced.

## Diagnosis efficiency

- **Manual estimate** — reference time for an SRE to read logs, correlate metrics and inspect
  code (95 minutes in the demo scenario).
- **AI elapsed** — classification + diagnosis + patch time.
- The dashboard shows both; the demo claim is roughly **3.2 min vs 95 min** for the mock
  scenario.

## Business value

Downtime in FinTech and e-commerce exceeds **$300,000/hour**. The pitch converts the measured
collapse-risk reduction into prevented incident cost:

```text
annual_savings ≈ incidents_per_year × avg_duration_h × 300_000 × collapse_risk_reduction
```

Example published run: p95 −95%, error rate −99%, reproducible collapse eliminated — the class
of incident is addressed, not hidden behind autoscaling on the same hardware.

## Why not just scale infrastructure

Autoscaling adds servers and hides architectural problems while increasing cloud cost. CDR's
numbers come from the same hardware profile, so the improvement is attributable to the code
change.

## Research context

- **ChaosEater** (ASE 2025 NIER): LLM-driven chaos engineering end-to-end, but only edits
  Kubernetes configuration, not application business logic.
- **AIOpsLab** (MLSys 2025, Microsoft Research + UC Berkeley + UIUC + IISc): benchmark of LLM
  agents across the incident lifecycle on Online Boutique. Best agent resolved only ~55% of
  mitigation cases despite ~100% detection — evidence that "diagnose" is largely solved and
  "fix" is the open bottleneck CDR attacks.

See also [[Research and Positioning]] and [[Hackathon Context]].
