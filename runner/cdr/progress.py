from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .config import Settings
from .models import (
    Diagnosis,
    Finding,
    Patch,
    Telemetry,
    Verification,
    utc_now,
)

PHASE_LABELS = {
    "chaos": "Chaos injection + collapse capture",
    "classification": "Root cause classification",
    "diagnosis": "Repository-aware diagnosis",
    "verification": "PR generation + resilience verification",
}


def _phase_row(run_id: str, phase: str, status: str, detail: str) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "phase": phase,
        "status": status,
        "label": PHASE_LABELS[phase],
        "detail": detail,
        "created_at": utc_now(),
    }


def _telemetry_rows(run_id: str, telemetry: Telemetry, kind: str) -> List[Dict[str, Any]]:
    return [
        {
            "run_id": run_id,
            "kind": kind,
            "t": sample.t,
            "p95": sample.p95,
            "p99": sample.p99,
            "error_rate": sample.error_rate,
            "rps": sample.rps,
        }
        for sample in telemetry.samples
    ]


class SupabaseProgress:
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

    def _patch_run(self, client: httpx.Client, run_id: str, payload: Dict[str, Any]) -> None:
        client.patch("/rest/v1/runs", params={"id": f"eq.{run_id}"}, json=payload)

    def _replace(
        self,
        client: httpx.Client,
        table: str,
        params: Dict[str, str],
        rows: List[Dict[str, Any]],
    ) -> None:
        client.delete(f"/rest/v1/{table}", params=params)
        if rows:
            client.post(f"/rest/v1/{table}", json=rows)

    def _upsert_phase(self, client: httpx.Client, run_id: str, row: Dict[str, Any]) -> None:
        self._replace(
            client,
            "run_phases",
            {"run_id": f"eq.{run_id}", "phase": f"eq.{row['phase']}"},
            [row],
        )

    def start(self, run_id: str, target_repo: str) -> None:
        self._safe(
            "start",
            lambda client: (
                self._patch_run(client, run_id, {"status": "running"}),
                self._upsert_phase(
                    client,
                    run_id,
                    _phase_row(
                        run_id,
                        "chaos",
                        "running",
                        f"spinning up the chaos scenario for {target_repo}",
                    ),
                ),
            ),
        )

    def handle(self, run_id: str, stage: str, payload: Dict[str, Any]) -> None:
        if stage == "chaos":
            self._handle_chaos(run_id, payload)
        elif stage == "classification":
            self._handle_classification(run_id, payload)
        elif stage == "diagnosis":
            self._handle_diagnosis(run_id, payload)
        elif stage == "verification":
            self._handle_verification(run_id, payload)

    def _handle_chaos(self, run_id: str, payload: Dict[str, Any]) -> None:
        telemetry: Telemetry = payload["telemetry"]
        collapsed = bool(payload["collapsed"])

        def action(client: httpx.Client) -> None:
            self._patch_run(client, run_id, {"status": "collapsed" if collapsed else "running"})
            self._upsert_phase(client, run_id, _phase_row(run_id, "chaos", "done", payload["detail"]))
            self._replace(
                client,
                "telemetry_samples",
                {"run_id": f"eq.{run_id}", "kind": "eq.before"},
                _telemetry_rows(run_id, telemetry, "before"),
            )

        self._safe("chaos", action)

    def _handle_classification(self, run_id: str, payload: Dict[str, Any]) -> None:
        finding: Finding = payload["finding"]

        def action(client: httpx.Client) -> None:
            self._patch_run(client, run_id, {"status": "diagnosing"})
            self._upsert_phase(
                client, run_id, _phase_row(run_id, "classification", "done", payload["detail"])
            )
            self._replace(
                client,
                "findings",
                {"run_id": f"eq.{run_id}"},
                [dict(finding.to_dict(), run_id=run_id)],
            )

        self._safe("classification", action)

    def _handle_diagnosis(self, run_id: str, payload: Dict[str, Any]) -> None:
        diagnosis: Diagnosis = payload["diagnosis"]
        patch: Patch = payload["patch"]
        finding: Finding = payload["finding"]

        def action(client: httpx.Client) -> None:
            self._patch_run(client, run_id, {"status": "patching"})
            self._upsert_phase(
                client, run_id, _phase_row(run_id, "diagnosis", "done", payload["detail"])
            )
            self._replace(
                client,
                "findings",
                {"run_id": f"eq.{run_id}"},
                [dict(finding.to_dict(), run_id=run_id)],
            )
            self._replace(
                client,
                "diagnoses",
                {"run_id": f"eq.{run_id}"},
                [dict(diagnosis.to_dict(), run_id=run_id)],
            )
            self._replace(
                client,
                "patches",
                {"run_id": f"eq.{run_id}"},
                [dict(patch.to_dict(), run_id=run_id)],
            )

        self._safe("diagnosis", action)

    def _handle_verification(self, run_id: str, payload: Dict[str, Any]) -> None:
        verification: Verification = payload["verification"]
        telemetry_after: Telemetry = payload["telemetry_after"]

        def action(client: httpx.Client) -> None:
            self._patch_run(client, run_id, {"status": "verifying"})
            self._upsert_phase(
                client,
                run_id,
                _phase_row(
                    run_id,
                    "verification",
                    "done" if verification.stable else "failed",
                    payload["detail"],
                ),
            )
            self._replace(
                client,
                "telemetry_samples",
                {"run_id": f"eq.{run_id}", "kind": "eq.after"},
                _telemetry_rows(run_id, telemetry_after, "after"),
            )
            self._replace(
                client,
                "verifications",
                {"run_id": f"eq.{run_id}"},
                [
                    dict(
                        {
                            "stable": verification.stable,
                            "before": verification.before.to_dict(),
                            "after": verification.after.to_dict(),
                            "improvement_pct": verification.improvement_pct,
                        },
                        run_id=run_id,
                    )
                ],
            )

        self._safe("verification", action)

    def _safe(self, stage: str, action) -> None:
        try:
            with self._client() as client:
                action(client)
            print(f"[cdr] progress: {stage} published")
        except Exception as error:
            print(f"[cdr] progress update {stage} skipped: {error}")
