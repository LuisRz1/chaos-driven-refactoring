# Live evidence — checkout email latency

Run `run-2738beb5` executed the real Docker Compose lab on September 27, 2026. k6 held 200
virtual users for 120 seconds and Toxiproxy injected 800 ms latency into `emailservice` at
second 30. IBM Bob then edited the pinned Online Boutique checkoutservice at commit
`cd1cb59f6fce3e2ccf08be7cea743e3784932d73`, the runner rebuilt its container, and the same
experiment was repeated.

| Signal | Before | After Bob |
| --- | ---: | ---: |
| p95 checkout latency | 919.6 ms | 691.1 ms |
| p99 checkout latency | 930.4 ms | 833.0 ms |
| Checkout error rate | 0% | 0% |
| Time to collapse | 30 s | No collapse |
| Throughput | 122.9 rps | 156.4 rps |

The p95 improvement was 24.8%, throughput increased 27.3%, and the collapse was eliminated
without bypassing payment or shipping. Bob added a 200 ms child context around the optional
confirmation-email RPC in `src/checkoutservice/main.go`; the order response remains successful
when email is slow.

IBM Bob evidence:

- Task id: `fdbad60b579de545555fd8ef043b9bf1`
- Cost: `0.083248` Bobcoins
- Duration: `15.89` seconds
- Files changed: one
- Session export: [`../bob_sessions/bobshell-email-latency-resilience-20260926-230514.json`](../bob_sessions/bobshell-email-latency-resilience-20260926-230514.json)

The full k6 JSONL captures and `verification.json` remain local under
`artifacts/run-2738beb5/live/`; they are intentionally gitignored because the raw captures total
hundreds of megabytes. The dashboard contains a downsampled series derived from those captures.
