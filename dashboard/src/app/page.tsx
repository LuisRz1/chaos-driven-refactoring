import { AnalyzeForm } from "@/components/analyze-form";
import { AutoRefresh } from "@/components/auto-refresh";
import { RunCard } from "@/components/run-card";
import { getRuns } from "@/lib/data";
import { formatDuration } from "@/lib/format";

export const dynamic = "force-dynamic";

const activeStatuses = ["queued", "running", "collapsed", "diagnosing", "patching", "verifying"];

const steps = [
  { phase: "01", name: "Inject chaos", detail: "k6 load + toxiproxy faults on a real target repo" },
  { phase: "02", name: "Classify", detail: "telemetry + logs → failure category with evidence" },
  { phase: "03", name: "Refactor", detail: "repository-aware diagnosis and generated patch" },
  { phase: "04", name: "Verify", detail: "same chaos scenario re-run on the patched code" },
];

export default async function Home() {
  const runs = await getRuns();
  const completed = runs.filter((run) => run.status === "completed");
  const collapsed = runs.filter((run) => run.collapse_detected);
  const p95Reductions = completed
    .map((run) => {
      const before = run.summary.p95_before_ms;
      const after = run.summary.p95_after_ms;
      if (!before || !after) {
        return null;
      }
      return ((before - after) / before) * 100;
    })
    .filter((value): value is number => typeof value === "number" && !Number.isNaN(value));
  const avgReduction =
    p95Reductions.length > 0
      ? p95Reductions.reduce((sum, value) => sum + value, 0) / p95Reductions.length
      : null;
  const aiMinutes = completed
    .map((run) => run.summary.diagnosis_minutes_ai)
    .filter((value): value is number => typeof value === "number" && !Number.isNaN(value));
  const avgAiMinutes =
    aiMinutes.length > 0 ? aiMinutes.reduce((sum, value) => sum + value, 0) / aiMinutes.length : null;
  const collapseTimes = collapsed
    .map((run) => run.summary.time_to_collapse_s)
    .filter((value): value is number => typeof value === "number" && !Number.isNaN(value));
  const avgCollapse =
    collapseTimes.length > 0
      ? collapseTimes.reduce((sum, value) => sum + value, 0) / collapseTimes.length
      : null;
  const hasActiveRuns = runs.some((run) => activeStatuses.includes(run.status));

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <p className="font-mono text-xs uppercase tracking-widest text-cyan-400">
          Resilience control plane
        </p>
        <h1 className="max-w-3xl text-3xl font-semibold tracking-tight sm:text-4xl">
          Break the system on purpose. Ship the architecture that survives it.
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-zinc-400">
          CDR injects load and faults into a real repository running in staging, captures the
          physical collapse, classifies the root cause, generates a refactor PR with full
          repository context and proves the fix by re-running the exact same scenario.
        </p>
      </section>

      <AnalyzeForm />

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Runs tracked
          </p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-zinc-100">{runs.length}</p>
          <p className="mt-1 text-xs text-zinc-500">{completed.length} completed</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Collapses captured
          </p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-rose-300">
            {collapsed.length}
          </p>
          <p className="mt-1 text-xs text-zinc-500">under identical load profiles</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Avg p95 reduction
          </p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-emerald-300">
            {avgReduction !== null ? `${avgReduction.toFixed(1)}%` : "—"}
          </p>
          <p className="mt-1 text-xs text-zinc-500">after verified fix</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Avg AI diagnosis
          </p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-cyan-300">
            {avgAiMinutes !== null ? `${avgAiMinutes.toFixed(1)} min` : "—"}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            vs {completed[0]?.summary.diagnosis_minutes_manual_estimate ?? 95} min manual SRE estimate
          </p>
        </div>
      </section>

      <section className="rounded-xl border border-white/10 bg-zinc-900/40 p-5">
        <h2 className="text-sm font-medium text-zinc-200">Pipeline</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step) => (
            <div key={step.phase} className="flex gap-3">
              <span className="font-mono text-xs text-cyan-400">{step.phase}</span>
              <div>
                <p className="text-sm font-medium text-zinc-200">{step.name}</p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-500">{step.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-medium text-zinc-200">Experiment runs</h2>
          <div className="flex items-center gap-3">
            <AutoRefresh active={hasActiveRuns} />
            <span className="text-xs text-zinc-500">
              {avgCollapse !== null
                ? `avg ${formatDuration(avgCollapse)} under chaos load before collapse`
                : "no collapse data yet"}
            </span>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {runs.map((run) => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
        {completed.length === 0 ? (
          <p className="text-xs text-zinc-500">
            No verified runs yet — start one with{" "}
            <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono">
              cdr run --scenario checkout-latency-cascade
            </code>
            .
          </p>
        ) : null}
      </section>
    </div>
  );
}
