from __future__ import annotations

from cdr.bisector import bisect_concurrency
from cdr.models import Finding, Telemetry, TelemetrySample


def _make_telemetry(log_signals: list[str]) -> Telemetry:
    sample = TelemetrySample(t=0, p95=200.0, p99=310.0, error_rate=0.05, rps=600.0)
    return Telemetry(
        samples=[sample],
        p95_ms=200.0,
        p99_ms=310.0,
        error_rate=0.05,
        rps=600.0,
        time_to_collapse_s=None,
        log_signals=log_signals,
    )


def _make_finding(file_path: str = "src/worker/lock.go", symbol: str = "acquireMutex") -> Finding:
    return Finding(
        category="concurrency",
        confidence=0.90,
        root_cause="lock contention under load",
        evidence=[],
        file_path=file_path,
        symbol=symbol,
    )


def test_top_candidate_is_finding_location() -> None:
    finding = _make_finding()
    telemetry = _make_telemetry(["mutex contention detected in worker pool"])
    candidates = bisect_concurrency(finding, telemetry)

    assert len(candidates) >= 1
    top = candidates[0]
    assert top.file_path == finding.file_path
    assert top.symbol == finding.symbol
    assert top.suspicion_score == 1.0


def test_max_candidates_is_respected() -> None:
    finding = _make_finding()
    telemetry = _make_telemetry(
        [
            "mutex timeout in scheduler",
            "race condition detected in cache layer",
            "lock contention on connection pool",
            "atomic counter overflow in metrics collector",
            "goroutine leak detected in handler",
        ]
    )

    for limit in (1, 2, 3):
        candidates = bisect_concurrency(finding, telemetry, max_candidates=limit)
        assert len(candidates) <= limit
        assert len(candidates) >= 1


def test_unknown_signal_still_returns_finding_location() -> None:
    finding = _make_finding(file_path="src/api/handler.py", symbol="process_request")
    telemetry = _make_telemetry(["completely unrelated log line with no known keywords"])
    candidates = bisect_concurrency(finding, telemetry)

    assert len(candidates) >= 1
    assert candidates[0].file_path == finding.file_path
    assert candidates[0].symbol == finding.symbol
    assert candidates[0].suspicion_score == 1.0


def test_top_candidate_has_highest_suspicion_score() -> None:
    finding = _make_finding()
    telemetry = _make_telemetry(
        [
            "race condition in scheduler",
            "mutex lock timeout",
        ]
    )
    candidates = bisect_concurrency(finding, telemetry, max_candidates=3)

    top_score = candidates[0].suspicion_score
    for candidate in candidates[1:]:
        assert candidate.suspicion_score <= top_score


def test_deterministic_ordering() -> None:
    finding = _make_finding()
    signals = [
        "race condition in goroutine pool",
        "lock contention on shared resource",
        "mutex deadlock detected",
    ]
    telemetry = _make_telemetry(signals)

    result_a = bisect_concurrency(finding, telemetry, max_candidates=3)
    result_b = bisect_concurrency(finding, telemetry, max_candidates=3)

    assert [c.suspicion_score for c in result_a] == [c.suspicion_score for c in result_b]
    assert [c.rationale for c in result_a] == [c.rationale for c in result_b]
