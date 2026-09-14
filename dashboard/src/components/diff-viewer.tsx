export function DiffViewer({ diff }: { diff: string }) {
  const lines = diff.split("\n");
  return (
    <pre className="max-h-96 overflow-auto rounded-lg border border-white/10 bg-black/60 p-4 font-mono text-xs leading-relaxed">
      {lines.map((line, index) => {
        let className = "text-zinc-400";
        if (line.startsWith("+++") || line.startsWith("---")) {
          className = "text-zinc-500";
        } else if (line.startsWith("+")) {
          className = "text-emerald-300 bg-emerald-500/10";
        } else if (line.startsWith("-")) {
          className = "text-rose-300 bg-rose-500/10";
        } else if (line.startsWith("@@")) {
          className = "text-cyan-300";
        }
        return (
          <div key={index} className={`px-1 ${className}`}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}
