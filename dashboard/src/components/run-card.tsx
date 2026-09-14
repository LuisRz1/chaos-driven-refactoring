import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import { formatDateTime, formatMs, formatPercent } from "@/lib/format";
import type { Run } from "@/lib/types";

export function RunCard({ run }: { run: Run }) {
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
            {formatPercent(run.summary.error_rate_before)} → {formatPercent(run.summary.error_rate_after)}
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
