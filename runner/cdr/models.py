from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class LoadConfig:
    tool: str = "k6"
    endpoint: str = ""
    vus: int = 200
    duration_s: int = 120
    injection_at_s: int = 30


@dataclass
class ChaosConfig:
    tool: str = "toxiproxy"
    proxy: str = "payment-service"
    fault: str = "latency"
    attributes: Dict[str, float] = field(default_factory=dict)


@dataclass
class Thresholds:
    p95_ms: float = 500.0
    error_rate: float = 0.05
    collapse_error_rate: float = 0.25


@dataclass
class Scenario:
    name: str
    target: str
    commit: str = "main"
    mode: str = "mock"
    load: LoadConfig = field(default_factory=LoadConfig)
    chaos: ChaosConfig = field(default_factory=ChaosConfig)
    thresholds: Thresholds = field(default_factory=Thresholds)


@dataclass
class TelemetrySample:
    t: int
    p95: float
    p99: float
    error_rate: float
    rps: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Telemetry:
    samples: List[TelemetrySample]
    p95_ms: float
    p99_ms: float
    error_rate: float
    rps: float
    time_to_collapse_s: Optional[float]
    log_signals: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "samples": [sample.to_dict() for sample in self.samples],
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "error_rate": self.error_rate,
            "rps": self.rps,
            "time_to_collapse_s": self.time_to_collapse_s,
            "log_signals": list(self.log_signals),
        }


@dataclass
class Finding:
    category: str
    confidence: float
    root_cause: str
    evidence: List[str]
    file_path: str
    symbol: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Diagnosis:
    model: str
    analysis_md: str
    proposed_change: str
    bob_task_id: Optional[str] = None
    bobcoins: Optional[float] = None
    target_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Patch:
    branch: str
    files_changed: List[str]
    diff: str
    pr_url: Optional[str] = None
    source: str = "template"
    bob_task_id: Optional[str] = None
    bobcoins: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricsSnapshot:
    p95_ms: float
    p99_ms: float
    error_rate: float
    time_to_collapse_s: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Verification:
    stable: bool
    before: MetricsSnapshot
    after: MetricsSnapshot
    improvement_pct: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["before"] = self.before.to_dict()
        payload["after"] = self.after.to_dict()
        return payload


@dataclass
class PhaseRecord:
    phase: str
    status: str
    label: str
    detail: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunResult:
    run_id: str
    scenario_name: str
    target_repo: str
    commit_sha: str
    mode: str
    status: str
    started_at: str
    finished_at: Optional[str]
    collapse_detected: bool
    summary: Dict[str, Any]
    telemetry: Telemetry
    telemetry_after: Optional[Telemetry]
    phases: List[PhaseRecord]
    finding: Finding
    diagnosis: Diagnosis
    patch: Patch
    verification: Verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_name": self.scenario_name,
            "target_repo": self.target_repo,
            "commit_sha": self.commit_sha,
            "mode": self.mode,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "collapse_detected": self.collapse_detected,
            "summary": self.summary,
            "telemetry": self.telemetry.to_dict(),
            "telemetry_after": self.telemetry_after.to_dict() if self.telemetry_after else None,
            "phases": [phase.to_dict() for phase in self.phases],
            "finding": self.finding.to_dict(),
            "diagnosis": self.diagnosis.to_dict(),
            "patch": self.patch.to_dict(),
            "verification": self.verification.to_dict(),
        }
