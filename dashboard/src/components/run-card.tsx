import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import { formatDateTime, formatMs, formatPercent } from "@/lib/format";
import { getRunProgress, isActiveStatus } from "@/lib/progress";
import type { Run } from "@/lib/types";

export function RunCard({ run }: { run: Run }) {
  const progress = getRunProgress(run);
  const active = isActiveStatus(run.status);
  const hasMetrics = run.status === "completed" || run.status === "failed";

  return (
    <Link
      href={`/runs/${run.id}`}
      className="group block rounded-xl border border-white/10 bg-zinc-900/60 p-5 transition hover:border-cyan-500/40 hover:bg-zinc-900"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs text-zinc-500">{run.id}</p>
          <h3 className="mt-1 text-base font-semibold text-zinc-100 group-hover:text-cyan-300">
            {run.scenario_name}
          </h3>
        </div>
        <StatusBadge status={run.status} />
      </div>

      {active ? (
        <div className="mt-4">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-cyan-300">{progress.label}</span>
            <span className="font-mono text-zinc-500">{progress.percent}%</span>
          </div>
          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-cyan-400 transition-all duration-700"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          {run.status === "queued" ? (
            <p className="mt-2 text-[11px] text-zinc-500">
              Queued — the worker will start it automatically
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
        <div>
          <p className="text-zinc-500">p95 before</p>
          <p className="mt-0.5 font-medium text-rose-300 tabular-nums">
            {formatMs(run.summary.p95_before_ms)}
          </p>
        </div>
        <div>
          <p className="text-zinc-500">p95 after</p>
          <p className="mt-0.5 font-medium text-emerald-300 tabular-nums">
            {formatMs(run.summary.p95_after_ms)}
          </p>
        </div>
        <div>
          <p className="text-zinc-500">error rate</p>
          <p className="mt-0.5 font-medium text-zinc-200 tabular-nums">
            {hasMetrics
              ? `${formatPercent(run.summary.error_rate_before)} → ${formatPercent(run.summary.error_rate_after)}`
              : "pending"}
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-[11px] text-zinc-500">
        <span className="font-mono">
          {run.target_repo}@{run.commit_sha}
        </span>
        <span>
          {run.mode} · {formatDateTime(run.started_at)}
        </span>
      </div>
    </Link>
  );
}
