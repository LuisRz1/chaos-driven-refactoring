import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const ALLOWED_SCENARIOS = ["checkout-latency-cascade", "payment-dependency-timeout"];
const ALLOWED_MODES = ["mock", "live"];

function parseRepo(input: string): string | null {
  const value = input
    .trim()
    .replace(/\.git$/, "")
    .replace(/\/$/, "");
  const match = value.match(/^(?:https?:\/\/github\.com\/)?([\w.-]+)\/([\w.-]+)$/);
  if (!match) {
    return null;
  }
  return `${match[1]}/${match[2]}`;
}

export async function POST(request: Request) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const schema = process.env.NEXT_PUBLIC_SUPABASE_SCHEMA ?? "cdr";
  if (!url || !serviceKey) {
    return NextResponse.json(
      { error: "Supabase service role is not configured on the server" },
      { status: 503 },
    );
  }

  const body = (await request.json().catch(() => null)) as {
    repoUrl?: string;
    commit?: string;
    scenario?: string;
    mode?: string;
  } | null;
  if (!body?.repoUrl) {
    return NextResponse.json({ error: "repoUrl is required" }, { status: 400 });
  }

  const repo = parseRepo(body.repoUrl);
  if (!repo) {
    return NextResponse.json(
      { error: "Use a GitHub repository URL or owner/repo format" },
      { status: 400 },
    );
  }

  const scenario = ALLOWED_SCENARIOS.includes(body.scenario ?? "")
    ? (body.scenario as string)
    : ALLOWED_SCENARIOS[0];
  const mode = ALLOWED_MODES.includes(body.mode ?? "") ? (body.mode as string) : "mock";
  const commit = (body.commit ?? "main").trim() || "main";
  const runId = `run-${crypto.randomUUID().slice(0, 8)}`;

  const client = createClient(url, serviceKey, { auth: { persistSession: false } });
  const { error } = await client.schema(schema).from("runs").insert({
    id: runId,
    scenario_id: scenario,
    scenario_name: scenario,
    status: "queued",
    mode,
    target_repo: repo,
    commit_sha: commit,
    started_at: new Date().toISOString(),
    collapse_detected: false,
    summary: {},
  });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ runId, repo, scenario, mode, commit }, { status: 201 });
}
