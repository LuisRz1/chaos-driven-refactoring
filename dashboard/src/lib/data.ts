import { getMockRunDetail, mockRuns } from "./mock-data";
import { getSupabaseClient } from "./supabase";
import type {
  Diagnosis,
  Finding,
  Patch,
  PhaseEvent,
  Run,
  RunDetail,
  TelemetrySample,
  Verification,
} from "./types";

type Row = Record<string, unknown>;

function mapRun(row: Row): Run {
  return row as unknown as Run;
}

function mapSample(row: Row): TelemetrySample {
  return {
    t: Number(row.t ?? row.offset_s ?? 0),
    p95: Number(row.p95 ?? 0),
    p99: Number(row.p99 ?? 0),
    errorRate: Number(row.error_rate ?? 0),
    rps: Number(row.rps ?? 0),
  };
}

export async function getRuns(): Promise<Run[]> {
  const client = getSupabaseClient();
  if (!client) {
    return mockRuns;
  }
  try {
    const { data, error } = await client
      .from("runs")
      .select("*")
      .order("started_at", { ascending: false })
      .limit(50);
    if (error || !data || data.length === 0) {
      return mockRuns;
    }
    return data.map((row) =>
      mapRun({
        ...row,
        scenario_name: (row as Row).scenario_name ?? (row as Row).scenario_id,
      }),
    );
  } catch {
    return mockRuns;
  }
}

export async function getRunDetail(id: string): Promise<RunDetail | null> {
  const client = getSupabaseClient();
  if (!client) {
    return getMockRunDetail(id);
  }
  try {
    const { data: runRow, error: runError } = await client
      .from("runs")
      .select("*")
      .eq("id", id)
      .maybeSingle();
    if (runError || !runRow) {
      return getMockRunDetail(id);
    }
    const run = mapRun({
      ...runRow,
      scenario_name: runRow.scenario_name ?? runRow.scenario_id,
    });

    const [{ data: phaseRows }, { data: sampleRows }, { data: findingRows }] =
      await Promise.all([
        client.from("run_phases").select("*").eq("run_id", id).order("created_at"),
        client.from("telemetry_samples").select("*").eq("run_id", id).order("t"),
        client.from("findings").select("*").eq("run_id", id).limit(1),
      ]);

    const finding = (findingRows?.[0] as Finding | undefined) ?? null;

    let diagnosis: Diagnosis | null = null;
    if (finding) {
      const { data } = await client
        .from("diagnoses")
        .select("*")
        .eq("run_id", id)
        .maybeSingle();
      diagnosis = (data as Diagnosis | null) ?? null;
    }

    const [{ data: patchRow }, { data: verificationRow }] = await Promise.all([
      client.from("patches").select("*").eq("run_id", id).maybeSingle(),
      client.from("verifications").select("*").eq("run_id", id).maybeSingle(),
    ]);

    const samples = (sampleRows ?? []).filter((row) => (row as Row).kind !== "after");
    const samplesAfter = (sampleRows ?? []).filter((row) => (row as Row).kind === "after");

    return {
      run,
      samples: samples.map(mapSample),
      samples_after: samplesAfter.length > 0 ? samplesAfter.map(mapSample) : null,
      phases: (phaseRows ?? []) as PhaseEvent[],
      finding,
      diagnosis,
      patch: (patchRow as Patch | null) ?? null,
      verification: (verificationRow as Verification | null) ?? null,
    };
  } catch {
    return getMockRunDetail(id);
  }
}
