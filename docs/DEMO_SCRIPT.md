# Demo script (3 minutes)

Target: one continuous story — the system physically collapses, CDR finds why, ships a fix and
proves resilience. Record at 1080p with the dashboard in a browser and a terminal visible.

## 0:00–0:25 — Problem

- Voice over: "In FinTech and e-commerce, downtime costs over $300k per hour. Chaos tools find the
  failure, APM finds the line of code, AI agents write code — but nothing closes the loop."
- Show the `README.md` hero and the architecture diagram in `docs/ARCHITECTURE.md`.

## 0:25–0:50 — The lab

- Show `infra/target/docker-compose.yml` and terminal:
  `docker compose -f infra/target/docker-compose.yml up -d`
- Inject the fault:
  `curl -X POST http://localhost:8474/proxies/payment-service/toxics ... latency 800ms`
- Start k6: `k6 run -e BASE_URL=http://localhost:8080 infra/load/checkout-load.js`
- Voice over: "800 ms of injected latency on the payment dependency is enough to collapse
  checkout."

## 0:50–1:20 — Run the pipeline

- Terminal: `python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode live --sink all`
- Or queue it from the dashboard ("Analyze a repository") and start the worker with
  `python -m cdr watch --pace 6`; the run card and detail page show the live progress bar moving
  through chaos → classification → diagnosis → verification.
- Cut to the dashboard `/` and open the run: collapse reproduced at 74.5 s, p95 4,820 ms, error
  rate 38.4%.
- Voice over: "Phase 1 captured the physical collapse."

## 1:20–1:50 — Classification and diagnosis

- Show the finding card: `unresilient_dependency`, confidence 93%, evidence (goroutines blocked,
  no deadline in repo scan).
- Show the diagnosis section (Granite) with the proposed refactor.
- Voice over: "With full repository context, CDR proves the payment call has no deadline, no retry
  budget and no circuit breaker — and proposes the exact change."

## 1:50–2:30 — Patch and verification

- Show the generated diff and PR link.
- Show the verification panel: p95 236 ms, error rate 0.4%, "STABLE AFTER FIX", improvements
  −95.1% / −99.0% / −100%.
- Voice over: "The same chaos scenario is re-executed against the patched code. No collapse."

## 2:30–3:00 — Business impact and Bob 2.0

- Show `docs/METRICS.md` numbers and the formula slide.
- Voice over: "Diagnosis drops from 95 minutes of SRE work to 3.2 minutes; the incident class is
  eliminated, not hidden behind autoscaling."
- Close on `bob_sessions/`: "Built with IBM Bob 2.0 — agent mode, parallel tasks and subagents —
  every task session exported for judging."

## Backup: 5-minute live walkthrough

1. Dashboard overview → run detail (1 min).
2. Terminal mock run end to end (1 min).
3. `bob_sessions/` tour (1 min).
4. Architecture and judging map (1 min).
5. Q&A buffer (1 min).

## Recording checklist

- [ ] Dashboard deployed and pre-populated with the completed run.
- [ ] Terminal font large enough to read on mobile.
- [ ] Chaos lab already pulled (images cached) before recording.
- [ ] No credentials visible anywhere on screen.
- [ ] `bob_sessions/` exports present before the final take.
