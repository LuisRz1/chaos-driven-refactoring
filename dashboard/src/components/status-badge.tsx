import type { RunStatus } from "@/lib/types";

const styles: Record<RunStatus, string> = {
  queued: "bg-zinc-500/15 text-zinc-300 ring-zinc-500/30",
  running: "bg-cyan-500/15 text-cyan-300 ring-cyan-500/30",
  collapsed: "bg-rose-500/15 text-rose-300 ring-rose-500/30",
  diagnosing: "bg-violet-500/15 text-violet-300 ring-violet-500/30",
  patching: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  verifying: "bg-blue-500/15 text-blue-300 ring-blue-500/30",
  completed: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  failed: "bg-rose-600/20 text-rose-300 ring-rose-600/40",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium uppercase tracking-wide ring-1 ring-inset ${styles[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
