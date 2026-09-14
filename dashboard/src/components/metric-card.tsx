import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  tone?: "default" | "good" | "bad" | "info";
}) {
  const valueTone = {
    default: "text-zinc-100",
    good: "text-emerald-300",
    bad: "text-rose-300",
    info: "text-cyan-300",
  }[tone];

  return (
    <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-4">
      <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p className={`mt-2 text-2xl font-semibold tabular-nums ${valueTone}`}>{value}</p>
      {sub ? <p className="mt-1 text-xs text-zinc-500">{sub}</p> : null}
    </div>
  );
}
