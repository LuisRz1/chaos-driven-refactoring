from __future__ import annotations

from typing import Dict, List, Tuple

from .models import Finding, Telemetry

CATEGORY_SIGNATURES: List[Tuple[str, Tuple[str, ...]]] = [
    ("concurrency", ("race condition", "lock contention", "data race", "mutex", "atomic")),
    ("memory_leak", ("memory leak", "out of memory", "oom", "heap growth", "gc pause")),
    ("db_saturation", ("connection pool", "max_connections", "too many connections", "n+1 query")),
    (
        "unresilient_dependency",
        ("deadline exceeded", "timeout", "circuit breaker", "connection reset", "connection refused"),
    ),
]

CATEGORY_LOCATIONS: Dict[str, Tuple[str, str]] = {
    "concurrency": ("src/checkoutservice/main.go", "PlaceOrder"),
    "memory_leak": ("src/recommendationservice/server.py", "GetRecommendations"),
    "db_saturation": ("src/productcatalogservice/server.go", "ListProducts"),
    "unresilient_dependency": ("src/checkoutservice/main.go", "PlaceOrder"),
    "unknown": ("unknown", "unknown"),
}

CATEGORY_ROOT_CAUSE: Dict[str, str] = {
    "concurrency": (
        "Concurrent access to shared checkout state without synchronization collapses under "
        "parallel load: workers contend on the same critical section and throughput degrades "
        "until timeouts cascade across the request path."
    ),
    "memory_leak": (
        "Request handlers retain references to per-request payloads after completion. Under "
        "sustained load the heap grows without bound and the runtime spends most cycles in GC "
        "until the service stops responding."
    ),
    "db_saturation": (
        "The service opens unbounded database connections and issues per-item queries inside a "
        "loop (N+1 pattern). Under burst load the database hits its connection limit and the "
        "whole catalog path errors out."
    ),
    "unresilient_dependency": (
        "The checkout path calls downstream services without a context deadline, retry budget or "
        "circuit breaker. Injected latency makes every request hold a worker until the transport "
        "timeout fires, so pools saturate and the checkout path collapses end to end."
    ),
    "unknown": (
        "Telemetry shows a reproducible collapse but the current rule set cannot attribute it to "
        "a known category. Manual review is required before proposing a refactor."
    ),
}


def classify(telemetry: Telemetry) -> Finding:
    haystack = " ".join(telemetry.log_signals).lower()
    category = "unknown"
    hits: List[str] = []

    for candidate, signatures in CATEGORY_SIGNATURES:
        matched = [signature for signature in signatures if signature in haystack]
        if len(matched) > len(hits):
            category = candidate
            hits = matched

    confidence = 0.93 if len(hits) >= 2 else 0.86 if len(hits) == 1 else 0.5
    file_path, symbol = CATEGORY_LOCATIONS[category]

    evidence = list(telemetry.log_signals)
    evidence.append(
        "collapse detected at t={}s under the same load profile".format(
            telemetry.time_to_collapse_s if telemetry.time_to_collapse_s is not None else "n/a"
        )
    )

    return Finding(
        category=category,
        confidence=confidence,
        root_cause=CATEGORY_ROOT_CAUSE[category],
        evidence=evidence,
        file_path=file_path,
        symbol=symbol,
    )
