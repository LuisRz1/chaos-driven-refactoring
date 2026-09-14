from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .config import Settings
from .models import RunResult
from .reporter import write_report


class StdoutSink:
    name = "stdout"

    def emit(self, result: RunResult) -> None:
        summary = result.summary
        print(f"[cdr] run {result.run_id} ({result.mode}) -> {result.status}")
        print(
            "[cdr] collapse={} p95 {}ms -> {}ms error {}% -> {}%".format(
                result.collapse_detected,
                summary.get("p95_before_ms"),
                summary.get("p95_after_ms"),
                summary.get("error_rate_before"),
                summary.get("error_rate_after"),
            )
        )
        print(f"[cdr] finding: {result.finding.category} (confidence {result.finding.confidence})")
        print(f"[cdr] stable after fix: {result.verification.stable}")


class JsonFileSink:
    name = "json"

    def __init__(self, artifacts_dir) -> None:
        self.artifacts_dir = artifacts_dir

    def emit(self, result: RunResult) -> None:
        report_path = write_report(result, self.artifacts_dir)
        print(f"[cdr] artifacts written to {report_path}")


class SupabaseSink:
    name = "supabase"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def headers(self) -> Dict[str, str]:
        schema = self.settings.supabase_schema
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
            "Accept-Profile": schema,
            "Content-Profile": schema,
        }

    def _insert(self, client: httpx.Client, table: str, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        response = client.post(f"/rest/v1/{table}", json=rows, headers=self.headers)
        if response.status_code >= 400:
            raise RuntimeError(
                f"insert into {table} failed: {response.status_code} {response.text[:300]}"
            )

    def emit(self, result: RunResult) -> None:
        base = self.settings.supabase_url.rstrip("/")
        run = {
            "id": result.run_id,
            "scenario_id": result.scenario_name,
            "scenario_name": result.scenario_name,
            "status": result.status,
            "mode": result.mode,
            "target_repo": result.target_repo,
            "commit_sha": result.commit_sha,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "collapse_detected": result.collapse_detected,
            "summary": result.summary,
        }
        phases = [
            {
                "run_id": result.run_id,
                "phase": phase.phase,
                "status": phase.status,
                "label": phase.label,
                "detail": phase.detail,
                "created_at": phase.created_at,
            }
            for phase in result.phases
        ]
        samples = [
            {
                "run_id": result.run_id,
                "kind": "before",
                "t": sample.t,
                "p95": sample.p95,
                "p99": sample.p99,
                "error_rate": sample.error_rate,
                "rps": sample.rps,
            }
            for sample in result.telemetry.samples
        ]
        if result.telemetry_after:
            samples.extend(
                {
                    "run_id": result.run_id,
                    "kind": "after",
                    "t": sample.t,
                    "p95": sample.p95,
                    "p99": sample.p99,
                    "error_rate": sample.error_rate,
                    "rps": sample.rps,
                }
                for sample in result.telemetry_after.samples
            )
        finding = dict(result.finding.to_dict(), run_id=result.run_id)
        diagnosis = dict(result.diagnosis.to_dict(), run_id=result.run_id)
        patch = dict(result.patch.to_dict(), run_id=result.run_id)
        verification = dict(
            {
                "stable": result.verification.stable,
                "before": result.verification.before.to_dict(),
                "after": result.verification.after.to_dict(),
                "improvement_pct": result.verification.improvement_pct,
            },
            run_id=result.run_id,
        )

        try:
            with httpx.Client(base_url=base, timeout=30) as client:
                self._insert(client, "runs", [run])
                self._insert(client, "run_phases", phases)
                self._insert(client, "telemetry_samples", samples)
                self._insert(client, "findings", [finding])
                self._insert(client, "diagnoses", [diagnosis])
                self._insert(client, "patches", [patch])
                self._insert(client, "verifications", [verification])
            print("[cdr] run synced to Supabase")
        except Exception as error:
            print(f"[cdr] supabase sync skipped: {error}")


def build_sinks(name: str, settings: Settings) -> List[Any]:
    sinks: List[Any] = []
    if name in ("stdout", "all"):
        sinks.append(StdoutSink())
    if name in ("json", "all"):
        sinks.append(JsonFileSink(settings.artifacts_dir))
    if name in ("supabase", "all") and settings.supabase_configured:
        sinks.append(SupabaseSink(settings))
    if not sinks:
        sinks.append(StdoutSink())
    return sinks


def emit_all(sinks: List[Any], result: RunResult) -> None:
    for sink in sinks:
        try:
            sink.emit(result)
        except Exception as error:
            print("[cdr] sink {} failed: {}".format(getattr(sink, "name", sink), error))
