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

function beforeSeries(): TelemetrySample[] {
  return [
    { t: 0, p95: 434.6, p99: 460.4, errorRate: 0, rps: 170.7 },
    { t: 6, p95: 79.8, p99: 90.5, errorRate: 0, rps: 186.3 },
    { t: 12, p95: 36.3, p99: 48.4, errorRate: 0, rps: 187.7 },
    { t: 18, p95: 27, p99: 30.7, errorRate: 0, rps: 186.7 },
    { t: 24, p95: 29, p99: 32, errorRate: 0, rps: 187.7 },
    { t: 30, p95: 918.4, p99: 927.3, errorRate: 0, rps: 117 },
    { t: 36, p95: 914.3, p99: 919.1, errorRate: 0, rps: 127.7 },
    { t: 42, p95: 925, p99: 936.8, errorRate: 0, rps: 122.7 },
    { t: 48, p95: 922.6, p99: 936.3, errorRate: 0, rps: 115 },
    { t: 54, p95: 921.5, p99: 930.4, errorRate: 0, rps: 106.3 },
    { t: 60, p95: 923.7, p99: 934.5, errorRate: 0, rps: 99.3 },
    { t: 66, p95: 923.2, p99: 939.3, errorRate: 0, rps: 99.7 },
    { t: 72, p95: 918.4, p99: 928.5, errorRate: 0, rps: 93.7 },
    { t: 78, p95: 923.2, p99: 926.4, errorRate: 0, rps: 92 },
    { t: 84, p95: 920.8, p99: 928.4, errorRate: 0, rps: 92.7 },
    { t: 90, p95: 918.7, p99: 925.3, errorRate: 0, rps: 95.7 },
    { t: 96, p95: 926, p99: 938.9, errorRate: 0, rps: 100 },
    { t: 102, p95: 931.5, p99: 940.5, errorRate: 0, rps: 106.7 },
    { t: 108, p95: 922.2, p99: 933.4, errorRate: 0, rps: 111.3 },
    { t: 114, p95: 925.5, p99: 929.7, errorRate: 0, rps: 108.7 },
    { t: 120, p95: 913.5, p99: 913.6, errorRate: 0, rps: 12 },
  ];
}

function afterSeries(): TelemetrySample[] {
  return [
    { t: 0, p95: 967.5, p99: 981.2, errorRate: 0, rps: 159.7 },
    { t: 6, p95: 725.1, p99: 738.1, errorRate: 0, rps: 167.7 },
    { t: 12, p95: 706.5, p99: 721.3, errorRate: 0, rps: 168 },
    { t: 18, p95: 531.9, p99: 566.2, errorRate: 0, rps: 165.7 },
    { t: 24, p95: 123.3, p99: 141, errorRate: 0, rps: 161.3 },
    { t: 30, p95: 277.1, p99: 291.4, errorRate: 0, rps: 149.3 },
    { t: 36, p95: 242.5, p99: 247.7, errorRate: 0, rps: 154.3 },
    { t: 42, p95: 244.8, p99: 257.8, errorRate: 0, rps: 156 },
    { t: 48, p95: 246, p99: 258.5, errorRate: 0, rps: 153.7 },
    { t: 54, p95: 241.4, p99: 248, errorRate: 0, rps: 156.3 },
    { t: 60, p95: 245.9, p99: 253.2, errorRate: 0, rps: 155 },
    { t: 66, p95: 249.1, p99: 257, errorRate: 0, rps: 150.7 },
    { t: 72, p95: 273.2, p99: 293.3, errorRate: 0, rps: 148.7 },
    { t: 78, p95: 258.8, p99: 269.9, errorRate: 0, rps: 154 },
    { t: 84, p95: 246.7, p99: 262, errorRate: 0, rps: 156.7 },
    { t: 90, p95: 241.8, p99: 247.2, errorRate: 0, rps: 153.7 },
    { t: 96, p95: 243.1, p99: 250.4, errorRate: 0, rps: 155 },
    { t: 102, p95: 243.4, p99: 260.7, errorRate: 0, rps: 154.7 },
    { t: 108, p95: 270.7, p99: 288.1, errorRate: 0, rps: 152.3 },
    { t: 114, p95: 259, p99: 270, errorRate: 0, rps: 155.7 },
    { t: 120, p95: 253.7, p99: 268.6, errorRate: 0, rps: 30 },
  ];
}

const runOne: Run = {
  id: "run-2738beb5",
  project_id: "project-online-boutique",
  scenario_id: "scenario-checkout-latency",
  scenario_name: "checkout-latency-cascade",
  status: "completed",
  mode: "live",
  target_repo: "GoogleCloudPlatform/microservices-demo",
  commit_sha: "cd1cb59",
  started_at: "2026-09-27T03:57:19Z",
  finished_at: "2026-09-27T04:11:41Z",
  collapse_detected: true,
  summary: {
    time_to_collapse_s: 30,
    p95_before_ms: 919.6,
    p99_before_ms: 930.4,
    error_rate_before: 0,
    p95_after_ms: 691.1,
    p99_after_ms: 833,
    error_rate_after: 0,
    stable_after_fix: true,
    diagnosis_minutes_manual_estimate: 90,
    diagnosis_minutes_ai: 0.3,
    pr_url: null,
    telemetry_source: "live",
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
  commit_sha: "cd1cb59",
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
    telemetry_source: "simulation",
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
    detail: "Real k6 load, 800 ms latency on email-service, reproducible collapse at 30s",
    created_at: "2026-09-27T03:57:19Z",
  },
  {
    id: "phase-2",
    run_id: runOne.id,
    phase: "classification",
    status: "done",
    label: "Root cause classification",
    detail: "unresilient_dependency (confidence 0.86) — optional email RPC exceeds the checkout budget",
    created_at: "2026-09-27T03:59:23Z",
  },
  {
    id: "phase-3",
    run_id: runOne.id,
    phase: "diagnosis",
    status: "done",
    label: "Repository-aware diagnosis",
    detail: "IBM Bob task fdbad60b applied a 200 ms child context to email confirmation",
    created_at: "2026-09-27T04:05:31Z",
  },
  {
    id: "phase-4",
    run_id: runOne.id,
    phase: "verification",
    status: "done",
    label: "PR generation + resilience verification",
    detail: "Same live scenario re-executed — stable, p95 691.1 ms, 0% errors, no collapse",
    created_at: "2026-09-27T04:11:41Z",
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
  confidence: 0.86,
  root_cause:
    "PlaceOrder waits synchronously for optional email confirmation using the request context. Injected email latency pushes checkout beyond its p95 budget even though email failure is already non-fatal.",
  evidence: [
    "Toxiproxy injected 800 ms latency on email-service at t=30s",
    "Checkout p95 reached 919.6 ms while the error rate stayed at 0%",
    "PlaceOrder blocks on sendOrderConfirmation even though failure is warning-only",
    "The same k6 scenario reproduced the threshold breach from t=30s onward",
  ],
  file_path: "src/checkoutservice/main.go",
  symbol: "PlaceOrder",
};

const diagnosisRunOne: Diagnosis = {
  id: "diagnosis-1",
  finding_id: findingRunOne.id,
  model: "bob-shell",
  analysis_md: [
    "## Analysis",
    "",
    "`PlaceOrder` completes payment, shipping and cart cleanup before synchronously calling the optional email service. The call inherits the full request context, so 800 ms of downstream latency is paid by every checkout even though an email error does not fail the order.",
    "",
    "## Proposed refactor",
    "",
    "1. Derive a 200 ms child context for the optional email confirmation RPC.",
    "2. Cancel the child context when `PlaceOrder` returns to release the timer.",
    "3. Preserve payment, shipping and successful order-response semantics.",
  ].join("\n"),
  proposed_change:
    "Bound optional email confirmation to 200 ms without changing mandatory checkout operations.",
  bob_task_id: "fdbad60b579de545555fd8ef043b9bf1",
  bobcoins: 0.083248,
  target_files: ["src/checkoutservice/main.go"],
};

const patchRunOne: Patch = {
  id: "patch-1",
  run_id: runOne.id,
  branch: "cdr/fix-checkout-email-latency",
  pr_url: null,
  files_changed: ["src/checkoutservice/main.go"],
  diff: [
    "--- a/src/checkoutservice/main.go",
    "+++ b/src/checkoutservice/main.go",
    "@@ -269,7 +269,9 @@ func (cs *checkoutService) PlaceOrder(ctx context.Context, req *pb.PlaceOrderReq",
    "-	if err := cs.sendOrderConfirmation(ctx, req.Email, orderResult); err != nil {",
    "+	emailCtx, emailCancel := context.WithTimeout(ctx, 200*time.Millisecond)",
    "+	defer emailCancel()",
    "+	if err := cs.sendOrderConfirmation(emailCtx, req.Email, orderResult); err != nil {",
  ].join("\n"),
  source: "bob-shell",
  bob_task_id: "fdbad60b579de545555fd8ef043b9bf1",
  bobcoins: 0.083248,
};

const verificationRunOne: Verification = {
  id: "verification-1",
  run_id: runOne.id,
  stable: true,
  before: { p95_ms: 919.6, p99_ms: 930.4, error_rate: 0, time_to_collapse_s: 30 },
  after: { p95_ms: 691.1, p99_ms: 833, error_rate: 0, time_to_collapse_s: null },
  improvement_pct: {
    p95: 24.8,
    p99: 10.5,
    error_rate: 0,
    collapse: 100,
    diagnosis_time: 99.7,
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
