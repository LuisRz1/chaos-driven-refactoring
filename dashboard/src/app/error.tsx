"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="max-w-md rounded-xl border border-white/10 bg-zinc-900/60 p-8 text-center">
        <p className="text-2xl">⚠️</p>
        <h1 className="mt-3 text-lg font-semibold text-zinc-100">
          This view could not be rendered
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">
          {error.message || "Unexpected server error while loading CDR data."}
        </p>
        <button
          onClick={reset}
          className="mt-5 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-medium text-zinc-950 transition hover:bg-cyan-400"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
