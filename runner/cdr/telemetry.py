from __future__ import annotations

import random
from typing import List, Optional

from .models import Scenario, Telemetry, TelemetrySample


def simulate_telemetry(scenario: Scenario, fixed: bool = False, seed: int = 42) -> Telemetry:
    rng = random.Random(seed)
    duration = scenario.load.duration_s
    injection_at = scenario.load.injection_at_s
    severity = max(0.35, min(1.0, scenario.load.vus / 200.0))
    ramp_window = max(20, min(45, int((duration - injection_at) * 0.6)))

    samples: List[TelemetrySample] = []
    for t in range(0, duration + 1, 3):
        injecting = injection_at <= t <= injection_at + ramp_window
        ramp = max(0.0, min(1.0, (t - injection_at) / ramp_window)) if t >= injection_at else 0.0
        noise = rng.uniform(-8, 8)

        if fixed:
            bump = 58 * severity if injecting else 0.0
            p95 = 204 + bump + noise
            error_rate = 0.32 + rng.uniform(0.0, 0.18)
            rps = 642 - bump * 0.4
        else:
            p95 = 182 + t * 0.9 + (ramp ** 2.4) * 3100 * severity * 1.4 + noise
            if t < injection_at + 15:
                error_rate = 0.2 + rng.uniform(0.0, 0.3)
            else:
                error_rate = min(38.4 * severity, (((t - injection_at - 15) / 33.0) ** 2) * 44 * severity)
            rps = 640 - (ramp ** 1.6) * 355 * severity

        samples.append(
            TelemetrySample(
                t=t,
                p95=round(max(60.0, p95), 1),
                p99=round(max(90.0, p95 * 1.55), 1),
                error_rate=round(max(0.0, error_rate), 2),
                rps=round(max(5.0, rps), 1),
            )
        )

    time_to_collapse = _detect_collapse(samples, scenario)
    peak_p95 = max(sample.p95 for sample in samples)
    final_error = samples[-1].error_rate
    signals = _log_signals(scenario, fixed, peak_p95, final_error)

    return Telemetry(
        samples=samples,
        p95_ms=round(peak_p95, 1),
        p99_ms=round(max(sample.p99 for sample in samples), 1),
        error_rate=round(final_error, 2),
        rps=round(sum(sample.rps for sample in samples) / len(samples), 1),
        time_to_collapse_s=time_to_collapse,
        log_signals=signals,
    )


def _detect_collapse(samples: List[TelemetrySample], scenario: Scenario) -> Optional[float]:
    for sample in samples:
        if sample.t < scenario.load.injection_at_s:
            continue
        if (
            sample.p95 > scenario.thresholds.p95_ms * 3
            or sample.error_rate > scenario.thresholds.collapse_error_rate * 100
        ):
            return float(sample.t)
    return None


def _log_signals(scenario: Scenario, fixed: bool, peak_p95: float, error_rate: float) -> List[str]:
    fault = scenario.chaos.fault
    proxy = scenario.chaos.proxy
    if fixed:
        return [
            f"circuit breaker opened on {proxy} and requests were shed with fallback",
            "context deadline of 400ms applied, no goroutine accumulation observed",
            "p95 stayed within threshold under identical chaos scenario",
        ]

    signals = [
        f"p95 on checkout.path rose to {peak_p95:.0f} ms under injected chaos",
        f"error rate peaked at {error_rate:.1f}% with 5xx responses",
    ]
    if fault in ("latency", "bandwidth"):
        signals.extend(
            [
                f"context deadline exceeded calling {proxy}",
                f"goroutines blocked in grpc.Invoke waiting for {proxy}",
                f"no deadline or circuit breaker found on the {proxy} client during repository scan",
            ]
        )
    elif fault == "abort":
        signals.extend(
            [
                f"connection reset by peer while calling {proxy}",
                f"transport: Error while dialing connection refused to {proxy}",
            ]
        )
    elif fault == "cpu":
        signals.extend(
            [
                "recommendationservice CPU saturating worker threads",
                "request queue depth growing without bound",
            ]
        )
    return signals
