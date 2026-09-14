"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const scenarioOptions = [
  { value: "checkout-latency-cascade", label: "Checkout latency cascade (payment latency)" },
  { value: "payment-dependency-timeout", label: "Payment dependency timeout (abort fault)" },
];

export function AnalyzeForm() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("GoogleCloudPlatform/microservices-demo");
  const [commit, setCommit] = useState("b9c7d2f");
  const [scenario, setScenario] = useState(scenarioOptions[0].value);
  const [mode, setMode] = useState("mock");
  const [status, setStatus] = useState<"idle" | "submitting" | "ok" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("submitting");
    setMessage("");
    try {
      const response = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repoUrl, commit, scenario, mode }),
      });
      const payload = (await response.json()) as { runId?: string; error?: string };
      if (!response.ok) {
        throw new Error(payload.error ?? "Request failed");
      }
      setStatus("ok");
      setMessage(`Queued as ${payload.runId} — the worker will analyze ${repoUrl} and publish results here.`);
      router.refresh();
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Request failed");
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-5"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium text-cyan-200">Analyze a repository</h2>
        <span className="text-[11px] text-zinc-500">
          Runtime analysis: IBM watsonx Granite · CDR built with IBM Bob 2.0
        </span>
      </div>
      <p className="mt-1 text-xs leading-relaxed text-zinc-400">
        Paste a GitHub repo. CDR queues a chaos run, classifies the collapse, proposes a refactor
        and verifies it. The worker executes queued runs with{" "}
        <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono">python -m cdr watch</code>.
      </p>

      <div className="mt-4 grid gap-3 lg:grid-cols-[2fr_1fr_1.5fr_0.8fr]">
        <label className="flex flex-col gap-1 text-xs text-zinc-400">
          Repository URL
          <input
            value={repoUrl}
            onChange={(event) => setRepoUrl(event.target.value)}
            placeholder="https://github.com/owner/repo"
            className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/60"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-zinc-400">
          Branch / commit
          <input
            value={commit}
            onChange={(event) => setCommit(event.target.value)}
            className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/60"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-zinc-400">
          Scenario
          <select
            value={scenario}
            onChange={(event) => setScenario(event.target.value)}
            className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/60"
          >
            {scenarioOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-zinc-400">
          Mode
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value)}
            className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/60"
          >
            <option value="mock">mock</option>
            <option value="live">live</option>
          </select>
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={status === "submitting"}
          className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-medium text-zinc-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {status === "submitting" ? "Queueing…" : "Run analysis"}
        </button>
        {message ? (
          <p
            className={`text-xs ${
              status === "error" ? "text-rose-300" : "text-emerald-300"
            }`}
          >
            {message}
          </p>
        ) : null}
      </div>
    </form>
  );
}
