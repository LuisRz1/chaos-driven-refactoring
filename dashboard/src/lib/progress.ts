import type { PhaseEvent, Run, RunStatus } from "./types";

const statusPercent: Record<RunStatus, number> = {
  queued: 3,
  running: 15,
  collapsed: 35,
  diagnosing: 60,
  patching: 80,
  verifying: 90,
  completed: 100,
  failed: 100,
};

const statusLabel: Record<RunStatus, string> = {
  queued: "Waiting for the worker to pick it up",
  running: "Injecting chaos and capturing telemetry",
  collapsed: "Collapse captured — classifying root cause",
  diagnosing: "Repository-aware diagnosis in progress",
  patching: "Generating the refactor patch",
  verifying: "Re-running chaos on the patched code",
  completed: "Analysis complete",
  failed: "Analysis failed",
};

const activeStatuses: RunStatus[] = [
  "queued",
  "running",
  "collapsed",
  "diagnosing",
  "patching",
  "verifying",
];

export interface RunProgress {
  percent: number;
  label: string;
  donePhases: number;
  totalPhases: number;
}

export function isActiveStatus(status: RunStatus): boolean {
  return activeStatuses.includes(status);
}

export function getRunProgress(run: Run, phases: PhaseEvent[] = []): RunProgress {
  const totalPhases = 4;
  if (phases.length > 0) {
    const donePhases = phases.filter(
      (phase) => phase.status === "done" || phase.status === "failed",
    ).length;
    const runningPhase = phases.find((phase) => phase.status === "running");
    const percent =
      run.status === "completed" || run.status === "failed"
        ? 100
        : Math.max(statusPercent.queued, Math.round((donePhases / totalPhases) * 100));
    return {
      percent,
      label: runningPhase?.label ?? statusLabel[run.status],
      donePhases,
      totalPhases,
    };
  }
  return {
    percent: statusPercent[run.status],
    label: statusLabel[run.status],
    donePhases: 0,
    totalPhases,
  };
}
