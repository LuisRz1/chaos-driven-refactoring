# Research and Positioning

Source material: the team's market research in
`../Contexto_Proyecto_CDR_IBM_Bob2_Hackathon.md`.

## Competitive landscape

| Competitor / approach | What it does | Why it falls short vs CDR |
| --- | --- | --- |
| Autoscaling (AWS Auto Scaling, KEDA) | adds servers under saturation | hides the architectural problem and increases cloud cost; does not fix code |
| Static analysis (SonarQube, Snyk) | scans code at rest for smells | cannot predict behavior under real load (50k concurrent users) |
| APM (New Relic, Datadog, Dynatrace) | locates the failing line via telemetry | stops at pointing; a human spends hours designing the refactor |
| AI code agents (Devin, Copilot Workspace) | write code from prompts/tickets | reactive, no connection to live telemetry, no autonomous verification |
| Chaos tooling (Gremlin, Chaos Mesh) | breaks the system safely | diagnoses only; a human interprets and rewrites manually |

CDR is the only end-to-end loop: physical collapse → root cause → code rewrite in the
application repository → verification under re-injected chaos.

## Academic state of the art (2025)

- **ChaosEater** (Kikuta et al., ASE 2025 NIER — "LLM-Powered Fully Automated Chaos
  Engineering"): automates hypothesis → experiment → analysis → improvement, but operates on
  Kubernetes manifests/configuration (e.g. fixing `restartPolicy`), not application business
  logic.
- **AIOpsLab** (Chen et al., MLSys 2025 — Microsoft Research, UC Berkeley, UIUC, IISc):
  benchmark for agents across detection, localization, diagnosis and mitigation on
  microservices in Kubernetes, using Online Boutique among its reference applications. Key
  data point: mitigation is the bottleneck — the best agent resolved only ~55% of mitigation
  cases despite ~100% detection; GPT-3.5 with shell resolved none.
- Repository-level repair research (2025) confirms that **full repository context** — versus
  isolated snippets — is the critical variable for correct LLM repairs, validating Bob 2.0's
  repository-aware approach.

## The three-part gap CDR occupies

No existing work combines all three:

1. diagnosis from real telemetry/infrastructure,
2. rewriting business logic inside the application source (not just K8s config),
3. autonomous verification by re-injecting the same chaos scenario against the fix.

## Pitch framing

- **Customer**: CTOs, DevOps leads, SRE teams in FinTech, e-commerce, streaming.
- **One-liner**: "CDR doesn't scale your servers to hide bad code; it breaks the system in a
  safe environment and uses IBM Bob 2.0 to rewrite the architecture, eradicating concurrency
  bottlenecks before they cost millions in production."
- Use the AIOpsLab mitigation statistic as external evidence that the problem is genuinely
  unsolved (strengthens Business Value and Originality at once).

Related: [[Metrics and Business Value]], [[Project Overview]].
