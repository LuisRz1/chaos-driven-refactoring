import type {
  Diagnosis,
  Finding,
  Patch,
  PhaseEvent,
  Run,
  RunDetail,
  TelemetrySample,
  Verification,
} from "./types";

function sample(t: number, p95: number, errorRate: number, rps: number): TelemetrySample {
  return {
    t,
    p95: Math.round(p95),
    p99: Math.round(p95 * 1.55),
    errorRate: Number(errorRate.toFixed(2)),
    rps: Math.round(rps),
  };
}

function beforeSeries(): TelemetrySample[] {
  const points: TelemetrySample[] = [];
  for (let t = 0; t <= 117; t += 3) {
    const injecting = t >= 30;
    const ramp = injecting ? Math.min(1, (t - 30) / 45) : 0;
    const p95 = 182 + t * 0.9 + Math.pow(ramp, 2.4) * 3100;
    const errorRate = t < 45 ? 0.2 : Math.min(38.4, Math.pow((t - 45) / 33, 2) * 44);
    const rps = 640 - Math.pow(ramp, 1.6) * 355;
    points.push(sample(t, p95, errorRate, rps));
  }
  return points;
}

function afterSeries(): TelemetrySample[] {
  const points: TelemetrySample[] = [];
  for (let t = 0; t <= 117; t += 3) {
    const injecting = t >= 30 && t <= 62;
    const bump = injecting ? Math.sin(((t - 30) / 32) * Math.PI) * 58 : 0;
    const p95 = 204 + bump + Math.sin(t / 6.5) * 12;
    const errorRate = 0.32 + Math.abs(Math.sin(t / 9)) * 0.18;
    const rps = 642 - bump * 0.4;
    points.push(sample(t, p95, errorRate, rps));
  }
  return points;
}

const runOne: Run = {
  id: "run-6f2a91c4",
  project_id: "project-online-boutique",
  scenario_id: "scenario-checkout-latency",
  scenario_name: "checkout-latency-cascade",
  status: "completed",
  mode: "live",
  target_repo: "GoogleCloudPlatform/microservices-demo",
  commit_sha: "b9c7d2f",
  started_at: "2026-09-25T16:12:04Z",
  finished_at: "2026-09-25T16:58:31Z",
  collapse_detected: true,
  summary: {
    time_to_collapse_s: 74.5,
    p95_before_ms: 4820,
    p99_before_ms: 7310,
    error_rate_before: 38.4,
    p95_after_ms: 236,
    p99_after_ms: 412,
    error_rate_after: 0.4,
    stable_after_fix: true,
    diagnosis_minutes_manual_estimate: 95,
    diagnosis_minutes_ai: 3.2,
    pr_url: "https://github.com/LuisRz1/microservices-demo/pull/1",
  },
};

const runTwo: Run = {
  id: "run-a3c81e07",
  project_id: "project-online-boutique",
  scenario_id: "scenario-payment-timeout",
  scenario_name: "payment-dependency-timeout",
  status: "verifying",
  mode: "mock",
  target_repo: "GoogleCloudPlatform/microservices-demo",
  commit_sha: "b9c7d2f",
  started_at: "2026-09-26T09:41:12Z",
  finished_at: null,
  collapse_detected: true,
  summary: {
    time_to_collapse_s: 61.8,
    p95_before_ms: 3980,
    p99_before_ms: 6120,
    error_rate_before: 31.7,
    p95_after_ms: null,
    p99_after_ms: null,
    error_rate_after: null,
    stable_after_fix: null,
    diagnosis_minutes_manual_estimate: 90,
    diagnosis_minutes_ai: 2.8,
    pr_url: null,
  },
};

export const mockRuns: Run[] = [runTwo, runOne];

const phasesRunOne: PhaseEvent[] = [
  {
    id: "phase-1",
    run_id: runOne.id,
    phase: "chaos",
    status: "done",
    label: "Chaos injection + collapse capture",
    detail: "k6 checkout load at 640 rps, toxiproxy latency 800ms on payment-service, collapse at 74.5s",
    created_at: "2026-09-25T16:12:04Z",
  },
  {
    id: "phase-2",
    run_id: runOne.id,
    phase: "classification",
    status: "done",
    label: "Root cause classification",
    detail: "unresilient_dependency (confidence 0.93) — gRPC call without deadline",
    created_at: "2026-09-25T16:34:22Z",
  },
  {
    id: "phase-3",
    run_id: runOne.id,
    phase: "diagnosis",
    status: "done",
    label: "Repository-aware diagnosis",
    detail: "granite-3-8b-instruct analyzed checkoutservice with full repo context",
    created_at: "2026-09-25T16:38:47Z",
  },
  {
    id: "phase-4",
    run_id: runOne.id,
    phase: "verification",
    status: "done",
    label: "PR generation + resilience verification",
    detail: "Same chaos scenario re-executed on patched code — stable, p95 236 ms",
    created_at: "2026-09-25T16:58:31Z",
  },
];

const phasesRunTwo: PhaseEvent[] = [
  {
    id: "phase-5",
    run_id: runTwo.id,
    phase: "chaos",
    status: "done",
    label: "Chaos injection + collapse capture",
    detail: "toxiproxy abort on payment-service, collapse at 61.8s",
    created_at: "2026-09-26T09:41:12Z",
  },
  {
    id: "phase-6",
    run_id: runTwo.id,
    phase: "classification",
    status: "done",
    label: "Root cause classification",
    detail: "unresilient_dependency (confidence 0.89)",
    created_at: "2026-09-26T09:52:03Z",
  },
  {
    id: "phase-7",
    run_id: runTwo.id,
    phase: "diagnosis",
    status: "done",
    label: "Repository-aware diagnosis",
    detail: "Proposed retry budget + circuit breaker on payment client",
    created_at: "2026-09-26T09:55:41Z",
  },
  {
    id: "phase-8",
    run_id: runTwo.id,
    phase: "verification",
    status: "running",
    label: "PR generation + resilience verification",
    detail: "Re-running chaos scenario on patched branch cdr/fix-payment-timeout",
    created_at: "2026-09-26T09:58:10Z",
  },
];

const findingRunOne: Finding = {
  id: "finding-1",
  run_id: runOne.id,
  category: "unresilient_dependency",
  confidence: 0.93,
  root_cause:
    "checkoutservice calls payment-service over gRPC without a context deadline, retry budget or circuit breaker. When injected latency raises payment latency above the caller timeout, checkout goroutines accumulate, thread pools saturate and the whole checkout path collapses.",
  evidence: [
    "p95 latency on checkout.path rose from 182 ms to 4,820 ms after injection",
    "61 goroutines blocked in grpc.Invoke on payment-service",
    "No deadline or circuit breaker found on the payment client in the repository scan",
    "Error rate 5xx peaked at 38.4% with deadline-exceeded signatures",
  ],
  file_path: "src/checkoutservice/main.go",
  symbol: "PlaceOrder",
};

const diagnosisRunOne: Diagnosis = {
  id: "diagnosis-1",
  finding_id: findingRunOne.id,
  model: "ibm/granite-3-8b-instruct",
  analysis_md: [
    "## Analysis",
    "",
    "`PlaceOrder` fans out to three downstream services. The payment leg uses the shared gRPC client with no per-call deadline and no failure isolation. Under injected latency every request holds a goroutine until the transport-level timeout fires, so throughput collapses long before errors surface.",
    "",
    "## Proposed refactor",
    "",
    "1. Apply a 400 ms `context.WithTimeout` deadline to the payment RPC.",
    "2. Add a retry budget with jitter (max 2 attempts) only for idempotent charge calls.",
    "3. Wrap the payment client with a circuit breaker that opens after 20 consecutive failures and half-opens after 5 s.",
    "4. Reuse the same pattern already present in `shippingservice` to stay consistent with the repository.",
  ].join("\n"),
  proposed_change:
    "Add context deadline, bounded retry with jitter and a circuit breaker around the payment RPC in PlaceOrder.",
};

const patchRunOne: Patch = {
  id: "patch-1",
  run_id: runOne.id,
  branch: "cdr/fix-checkout-payment-timeout",
  pr_url: "https://github.com/LuisRz1/microservices-demo/pull/1",
  files_changed: ["src/checkoutservice/main.go"],
  diff: [
    "--- a/src/checkoutservice/main.go",
    "+++ b/src/checkoutservice/main.go",
    "@@ -184,9 +184,16 @@ func (cs *checkoutService) PlaceOrder(ctx context.Context, req *pb.PlaceOrderReq) (*pb.PlaceOrderResp, error) {",
    "-	resp, err := cs.paymentSvc.Charge(ctx, &pb.ChargeRequest{",
    "+	payCtx, cancel := context.WithTimeout(ctx, 400*time.Millisecond)",
    "+	defer cancel()",
    "+",
    "+	resp, err := cs.paymentBreaker.Execute(func() (any, error) {",
    "+		return cs.paymentSvc.Charge(payCtx, &pb.ChargeRequest{",
    "			Amount: &pb.Money{CurrencyCode: req.GetCurrencyCode(), Units: total.Units},",
    "			CreditCard: req.GetCreditCard(),",
    "-	})",
    "+		})",
    "+	})",
    "	if err != nil {",
    "-		return nil, status.Errorf(codes.Internal, \"payment failed: %v\", err)",
    "+		return nil, status.Errorf(codes.Unavailable, \"payment unavailable: %v\", err)",
    "	}",
  ].join("\n"),
};

const verificationRunOne: Verification = {
  id: "verification-1",
  run_id: runOne.id,
  stable: true,
  before: { p95_ms: 4820, p99_ms: 7310, error_rate: 38.4, time_to_collapse_s: 74.5 },
  after: { p95_ms: 236, p99_ms: 412, error_rate: 0.4, time_to_collapse_s: null },
  improvement_pct: {
    p95: 95.1,
    p99: 94.4,
    error_rate: 99.0,
    collapse: 100,
    diagnosis_time: 96.6,
  },
};

const mockDetails: Record<string, RunDetail> = {
  [runOne.id]: {
    run: runOne,
    samples: beforeSeries(),
    samples_after: afterSeries(),
    phases: phasesRunOne,
    finding: findingRunOne,
    diagnosis: diagnosisRunOne,
    patch: patchRunOne,
    verification: verificationRunOne,
  },
  [runTwo.id]: {
    run: runTwo,
    samples: beforeSeries().map((point) => ({ ...point, t: point.t, p95: Math.round(point.p95 * 0.84) })),
    samples_after: null,
    phases: phasesRunTwo,
    finding: { ...findingRunOne, id: "finding-2", run_id: runTwo.id, confidence: 0.89 },
    diagnosis: { ...diagnosisRunOne, id: "diagnosis-2", finding_id: "finding-2" },
    patch: {
      ...patchRunOne,
      id: "patch-2",
      run_id: runTwo.id,
      branch: "cdr/fix-payment-timeout",
      pr_url: null,
    },
    verification: null,
  },
};

export function getMockRunDetail(id: string): RunDetail | null {
  return mockDetails[id] ?? null;
}
