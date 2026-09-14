import type { PhaseEvent, PhaseStatus } from "@/lib/types";

const statusDot: Record<PhaseStatus, string> = {
  pending: "border-zinc-600 bg-zinc-900",
  running: "border-cyan-400 bg-cyan-400/20 animate-pulse",
  done: "border-emerald-400 bg-emerald-400",
  failed: "border-rose-500 bg-rose-500",
};

const statusText: Record<PhaseStatus, string> = {
  pending: "text-zinc-500",
  running: "text-cyan-300",
  done: "text-emerald-300",
  failed: "text-rose-300",
};

export function PhaseTimeline({ phases }: { phases: PhaseEvent[] }) {
  return (
    <ol className="relative space-y-6 border-l border-white/10 pl-6">
      {phases.map((phase) => (
        <li key={phase.id} className="relative">
          <span
            className={`absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 ${statusDot[phase.status]}`}
          />
          <div className="flex items-center gap-2">
            <p className={`text-sm font-medium ${statusText[phase.status]}`}>
              {phase.label}
            </p>
          </div>
          {phase.detail ? (
            <p className="mt-1 text-xs leading-relaxed text-zinc-400">{phase.detail}</p>
          ) : null}
          <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-zinc-600">
            {phase.phase} · {phase.status}
          </p>
        </li>
      ))}
    </ol>
  );
}
