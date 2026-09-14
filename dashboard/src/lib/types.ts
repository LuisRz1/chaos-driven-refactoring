export type RunStatus =
  | "queued"
  | "running"
  | "collapsed"
  | "diagnosing"
  | "patching"
  | "verifying"
  | "completed"
  | "failed";

export type RunMode = "mock" | "live";

export type PhaseName = "chaos" | "classification" | "diagnosis" | "verification";

export type PhaseStatus = "pending" | "running" | "done" | "failed";

export type FailureCategory =
  | "concurrency"
  | "memory_leak"
  | "unresilient_dependency"
  | "db_saturation"
  | "unknown";

export interface RunSummary {
  time_to_collapse_s: number | null;
  p95_before_ms: number | null;
  p99_before_ms: number | null;
  error_rate_before: number | null;
  p95_after_ms: number | null;
  p99_after_ms: number | null;
  error_rate_after: number | null;
  stable_after_fix: boolean | null;
  diagnosis_minutes_manual_estimate: number | null;
  diagnosis_minutes_ai: number | null;
  pr_url: string | null;
}

export interface Run {
  id: string;
  project_id: string;
  scenario_id: string;
  scenario_name: string;
  status: RunStatus;
  mode: RunMode;
  target_repo: string;
  commit_sha: string;
  started_at: string;
  finished_at: string | null;
  collapse_detected: boolean;
  summary: RunSummary;
}

export interface TelemetrySample {
  t: number;
  p95: number;
  p99: number;
  errorRate: number;
  rps: number;
}

export interface PhaseEvent {
  id: string;
  run_id: string;
  phase: PhaseName;
  status: PhaseStatus;
  label: string;
  detail: string | null;
  created_at: string;
}

export interface Finding {
  id: string;
  run_id: string;
  category: FailureCategory;
  confidence: number;
  root_cause: string;
  evidence: string[];
  file_path: string;
  symbol: string;
}

export interface Diagnosis {
  id: string;
  finding_id: string;
  model: string;
  analysis_md: string;
  proposed_change: string;
  bob_task_id?: string | null;
  bobcoins?: number | null;
  target_files?: string[] | null;
}

export interface Patch {
  id: string;
  run_id: string;
  branch: string;
  pr_url: string | null;
  files_changed: string[];
  diff: string;
  source?: string | null;
  bob_task_id?: string | null;
  bobcoins?: number | null;
}

export interface MetricsSnapshot {
  p95_ms: number;
  p99_ms: number;
  error_rate: number;
  time_to_collapse_s: number | null;
}

export interface Verification {
  id: string;
  run_id: string;
  stable: boolean;
  before: MetricsSnapshot;
  after: MetricsSnapshot;
  improvement_pct: Record<string, number>;
}

export interface RunDetail {
  run: Run;
  samples: TelemetrySample[];
  samples_after: TelemetrySample[] | null;
  phases: PhaseEvent[];
  finding: Finding | null;
  diagnosis: Diagnosis | null;
  patch: Patch | null;
  verification: Verification | null;
}
