from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .config import Settings
from .models import RunResult
from .reporter import write_report

CHILD_TABLES = [
    "run_phases",
    "telemetry_samples",
    "findings",
    "diagnoses",
    "patches",
    "verifications",
]


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

    def emit_update(self, result: RunResult) -> None:
        self.emit(result)


class JsonFileSink:
    name = "json"

    def __init__(self, artifacts_dir) -> None:
        self.artifacts_dir = artifacts_dir

    def emit(self, result: RunResult) -> None:
        report_path = write_report(result, self.artifacts_dir)
        print(f"[cdr] artifacts written to {report_path}")

    def emit_update(self, result: RunResult) -> None:
        self.emit(result)


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

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.settings.supabase_url.rstrip("/"),
            timeout=30,
            headers=self.headers,
        )

    def _insert(self, client: httpx.Client, table: str, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        response = client.post(f"/rest/v1/{table}", json=rows)
        if response.status_code >= 400:
            raise RuntimeError(
                f"insert into {table} failed: {response.status_code} {response.text[:300]}"
            )

    def _run_payload(self, result: RunResult, include_id: bool) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "scenario_id": result.scenario_name,
            "scenario_name": result.scenario_name,
            "status": result.status,
            "mode": result.mode,
            "target_repo": result.target_repo,
            "commit_sha": result.commit_sha,
            "finished_at": result.finished_at,
            "collapse_detected": result.collapse_detected,
            "summary": result.summary,
        }
        if include_id:
            payload["id"] = result.run_id
            payload["started_at"] = result.started_at
        return payload

    def _children(self, result: RunResult) -> Dict[str, List[Dict[str, Any]]]:
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
        return {
            "run_phases": phases,
            "telemetry_samples": samples,
            "findings": [finding],
            "diagnoses": [diagnosis],
            "patches": [patch],
            "verifications": [verification],
        }

    def emit(self, result: RunResult) -> None:
        try:
            with self._client() as client:
                self._insert(client, "runs", [self._run_payload(result, include_id=True)])
                children = self._children(result)
                for table in CHILD_TABLES:
                    self._insert(client, table, children[table])
            print("[cdr] run synced to Supabase")
        except Exception as error:
            print(f"[cdr] supabase sync skipped: {error}")

    def emit_update(self, result: RunResult) -> None:
        try:
            with self._client() as client:
                response = client.patch(
                    "/rest/v1/runs",
                    params={"id": f"eq.{result.run_id}"},
                    json=self._run_payload(result, include_id=False),
                )
                if response.status_code >= 400:
                    raise RuntimeError(
                        f"update run failed: {response.status_code} {response.text[:300]}"
                    )
                for table in CHILD_TABLES:
                    client.delete(f"/rest/v1/{table}", params={"run_id": f"eq.{result.run_id}"})
                children = self._children(result)
                for table in CHILD_TABLES:
                    self._insert(client, table, children[table])
            print("[cdr] queued run updated in Supabase")
        except Exception as error:
            print(f"[cdr] supabase update failed: {error}")


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


def emit_update_all(sinks: List[Any], result: RunResult) -> None:
    for sink in sinks:
        try:
            update = getattr(sink, "emit_update", sink.emit)
            update(result)
        except Exception as error:
            print("[cdr] sink {} failed: {}".format(getattr(sink, "name", sink), error))
