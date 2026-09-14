# Metrics

CDR reports four families of metrics. All before/after comparisons run under an **identical load
profile and fault injection**, which is the core methodological claim of the project.

## 1. Latency

- **p95 / p99** — captured from the load generator summary for each run window.
- **Before** is measured during the chaos run that produces the collapse; **after** is measured by
  re-executing the exact same scenario against the patched code.

## 2. Reliability

- **Error rate** — share of failed requests (5xx, timeouts) over the run window.
- **Time to collapse** — seconds from the start of the run until p95 crosses 3× the configured
  threshold or the error rate crosses the collapse threshold. `null` after the fix means no
  collapse was reproduced.

## 3. Diagnosis efficiency

- **Manual estimate** — reference time for an SRE to read logs, correlate metrics and inspect the
  code (default: 95 minutes in the demo scenario).
- **AI elapsed** — time the pipeline takes to classify, diagnose and propose the patch
  (mock-mode runs complete in seconds; reported value is modeled from the phase work).
- **Reduction** — `(manual − ai) / manual`.

## 4. Business value

Downtime in FinTech and e-commerce exceeds **$300,000/hour**. The pitch translates the measured
probability-of-collapse reduction into prevented incident cost:

```
annual_savings ≈ incidents_per_year × avg_duration_h × 300_000 × collapse_risk_reduction
```

The published run in the demo reduces p95 by ~95%, error rate by ~99% and eliminates the
reproducible collapse — evidence that the class of incident is addressed, not hidden behind
infrastructure scaling.

## Why not just scale infrastructure

Autoscaling adds servers and hides architectural problems while increasing cloud cost. CDR's
before/after numbers are produced on the same hardware profile, so the improvement is attributable
to the code change, not to capacity.

## Research context

The 2025 academic state of the art (ChaosEater, ASE 2025 NIER; AIOpsLab, MLSys 2025) shows that
LLM agents already diagnose cloud incidents reasonably well but **fail systematically at
mitigation** — AIOpsLab's best agent resolved only ~55% of mitigation cases. CDR targets exactly
that gap: producing a repository-aware patch and proving it under the same chaos scenario.
