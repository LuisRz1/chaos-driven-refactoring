# CDR staging infrastructure

Minimal, reproducible chaos lab for the Online Boutique subset used by the CDR demo.

## Layout

| Path | Purpose |
| --- | --- |
| `target/docker-compose.yml` | Online Boutique subset (frontend, checkout, payment, catalog, cart, currency, shipping, email, redis) |
| `chaos/toxiproxy.json` | Toxiproxy proxy that sits between `checkoutservice` and `paymentservice` |
| `load/checkout-load.js` | k6 scenario: 200 virtual users driving add-to-cart and checkout |

## Start staging

```bash
docker compose -f infra/target/docker-compose.yml up -d
# wait for healthy services, then verify the storefront
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
```

## Inject chaos

```bash
# 800 ms latency (+/- 100 ms) on every payment call
curl -s -X POST http://localhost:8474/proxies/payment-service/toxics \
  -H "Content-Type: application/json" \
  -d '{"name":"latency","type":"latency","attributes":{"latency":800,"jitter":100}}'

# abort the dependency completely
curl -s -X POST http://localhost:8474/proxies/payment-service/toxics \
  -H "Content-Type: application/json" \
  -d '{"name":"abort","type":"abort","attributes":{"timeout":0}}'

# remove the injected fault
curl -s -X DELETE http://localhost:8474/proxies/payment-service/toxics/latency
```

## Generate load and capture the collapse

```bash
k6 run -e BASE_URL=http://localhost:8080 infra/load/checkout-load.js
```

Watch `http_req_duration{p95}` jump after the toxic is applied — that is the physical
collapse captured by phase 1 of the runner.

## Wire it to the runner

The runner ships with `--mode mock` (deterministic, no Docker) for pipeline and dashboard
development. Live mode uses these same endpoints; point `PAYMENT_SERVICE_ADDR` at
`toxiproxy:8666` (already configured in the compose file) and keep the toxiproxy admin API on
`localhost:8474` reachable from the runner.
