from __future__ import annotations

from .models import MetricsSnapshot, Scenario, Telemetry, Verification


def snapshot(telemetry: Telemetry) -> MetricsSnapshot:
    return MetricsSnapshot(
        p95_ms=telemetry.p95_ms,
        p99_ms=telemetry.p99_ms,
        error_rate=telemetry.error_rate,
        time_to_collapse_s=telemetry.time_to_collapse_s,
    )


def improvement_pct(before: float, after: float) -> float:
    if before <= 0:
        return 0.0
    return round(max(0.0, (before - after) / before * 100.0), 1)


def verify(before: Telemetry, after: Telemetry, scenario: Scenario) -> Verification:
    before_snapshot = snapshot(before)
    after_snapshot = snapshot(after)
    stable = (
        after.time_to_collapse_s is None
        and after.p95_ms <= scenario.thresholds.p95_ms * 1.5
        and after.error_rate <= max(1.0, scenario.thresholds.error_rate * 100 * 2)
    )
    collapse_improvement = (
        100.0 if before.time_to_collapse_s is not None and after.time_to_collapse_s is None else 0.0
    )
    improvements = {
        "p95": improvement_pct(before.p95_ms, after.p95_ms),
        "p99": improvement_pct(before.p99_ms, after.p99_ms),
        "error_rate": improvement_pct(before.error_rate, after.error_rate),
        "collapse": collapse_improvement,
    }
    return Verification(
        stable=stable,
        before=before_snapshot,
        after=after_snapshot,
        improvement_pct=improvements,
    )
