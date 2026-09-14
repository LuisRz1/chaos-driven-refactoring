from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .config import Settings
from .models import ChaosConfig, LoadConfig, Scenario, Thresholds
from .scenario import load_scenario

DEFAULT_SCENARIOS_DIR = None


class SupabaseQueue:
    def __init__(self, settings: Settings, scenarios_dir=None) -> None:
        self.settings = settings
        from pathlib import Path

        self.scenarios_dir = Path(scenarios_dir or Path(__file__).resolve().parents[1] / "scenarios")

    @property
    def _headers(self) -> Dict[str, str]:
        schema = self.settings.supabase_schema
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            "Accept-Profile": schema,
            "Content-Profile": schema,
        }

    def claim_next(self) -> Optional[Dict[str, Any]]:
        base = self.settings.supabase_url.rstrip("/")
        with httpx.Client(base_url=base, timeout=30, headers=self._headers) as client:
            response = client.get(
                "/rest/v1/runs",
                params={
                    "select": "*",
                    "status": "eq.queued",
                    "order": "started_at.asc",
                    "limit": "1",
                },
            )
            response.raise_for_status()
            rows = response.json()
            if not rows:
                return None
            row = rows[0]
            claimed = client.patch(
                "/rest/v1/runs",
                params={"id": f"eq.{row['id']}", "status": "eq.queued"},
                json={"status": "running"},
                headers={"Prefer": "return=representation"},
            )
            claimed.raise_for_status()
            updated = claimed.json()
            if not updated:
                return None
            row.update(updated[0])
            return row

    def mark_failed(self, run_id: str, reason: str) -> None:
        base = self.settings.supabase_url.rstrip("/")
        with httpx.Client(base_url=base, timeout=30, headers=self._headers) as client:
            client.patch(
                "/rest/v1/runs",
                params={"id": f"eq.{run_id}"},
                json={
                    "status": "failed",
                    "summary": {"error": reason[:500]},
                },
            )

    def scenario_for(self, row: Dict[str, Any]) -> Scenario:
        name = str(row.get("scenario_name") or row.get("scenario_id") or "checkout-latency-cascade")
        path = self.scenarios_dir / f"{name}.yaml"
        if path.exists():
            scenario = load_scenario(path)
        else:
            scenario = Scenario(
                name=name,
                target=str(row.get("target_repo") or "unknown/unknown"),
                commit=str(row.get("commit_sha") or "main"),
                mode=str(row.get("mode") or "mock"),
                load=LoadConfig(),
                chaos=ChaosConfig(),
                thresholds=Thresholds(),
            )
        scenario.target = str(row.get("target_repo") or scenario.target)
        scenario.commit = str(row.get("commit_sha") or scenario.commit)
        scenario.mode = str(row.get("mode") or scenario.mode)
        return scenario
