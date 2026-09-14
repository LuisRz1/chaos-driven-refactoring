from __future__ import annotations

from typing import Dict, Tuple

from .config import Settings
from .models import Diagnosis, Finding, Scenario, Telemetry
from .watsonx import WatsonxClient

FALLBACK_ANALYSIS: Dict[str, Tuple[str, str]] = {
    "unresilient_dependency": (
        "\n".join(
            [
                "## Analysis",
                "",
                "The failing path fans out to downstream services over gRPC. The dependency leg "
                "uses a shared client with no per-call deadline and no failure isolation. Under "
                "injected latency every request holds a worker until the transport timeout fires, "
                "so throughput collapses long before errors surface.",
                "",
                "## Proposed refactor",
                "",
                "1. Apply a 400 ms context deadline to the dependency call.",
                "2. Add a bounded retry with jitter only for idempotent operations.",
                "3. Wrap the client with a circuit breaker that opens after consecutive failures "
                "and half-opens after 5 s.",
                "4. Reuse the resilience pattern already present in the shipping service for "
                "consistency with the repository.",
            ]
        ),
        "Add context deadline, bounded retry with jitter and a circuit breaker around the dependency call.",
    ),
    "concurrency": (
        "\n".join(
            [
                "## Analysis",
                "",
                "The hot path mutates shared state from multiple goroutines without coordination. "
                "Under parallel load, contention on the same critical section serializes requests "
                "and latency grows until upstream timeouts cascade.",
                "",
                "## Proposed refactor",
                "",
                "1. Replace the coarse lock with a sharded lock keyed by cart id.",
                "2. Move non-critical work (logging, metrics) outside the critical section.",
                "3. Use atomic counters for the hot read path.",
            ]
        ),
        "Shard the critical section by key and remove non-essential work from the locked path.",
    ),
    "memory_leak": (
        "\n".join(
            [
                "## Analysis",
                "",
                "Handlers keep references to per-request payloads in module-level caches after the "
                "request completes. Under sustained load the heap grows until GC pressure stalls "
                "the service.",
                "",
                "## Proposed refactor",
                "",
                "1. Bound the cache with an LRU policy and TTL.",
                "2. Release payload references in a finally block.",
                "3. Emit heap metrics to make the regression visible in staging.",
            ]
        ),
        "Bound the cache with LRU+TTL and release per-request references deterministically.",
    ),
    "db_saturation": (
        "\n".join(
            [
                "## Analysis",
                "",
                "The catalog path issues one query per item and opens a connection per request. "
                "Under burst load the database reaches its connection limit and the whole path "
                "fails.",
                "",
                "## Proposed refactor",
                "",
                "1. Replace per-item queries with a batched IN query.",
                "2. Introduce a bounded connection pool shared by the service.",
                "3. Add a short statement timeout to fail fast.",
            ]
        ),
        "Batch item queries and introduce a bounded shared connection pool.",
    ),
}

DEFAULT_FALLBACK = (
    "## Analysis\n\nTelemetry shows a reproducible collapse. Manual review is required.\n",
    "Manual review required before proposing a refactor.",
)


class Diagnoser:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = WatsonxClient(settings)

    def diagnose(self, scenario: Scenario, finding: Finding, telemetry: Telemetry) -> Diagnosis:
        if self.client.configured:
            try:
                return self._diagnose_with_watsonx(scenario, finding, telemetry)
            except Exception:
                pass
        return self._fallback(finding)

    def _fallback(self, finding: Finding) -> Diagnosis:
        analysis, proposed = FALLBACK_ANALYSIS.get(finding.category, DEFAULT_FALLBACK)
        return Diagnosis(
            model="rule-based-fallback",
            analysis_md=analysis,
            proposed_change=proposed,
        )

    def _diagnose_with_watsonx(
        self, scenario: Scenario, finding: Finding, telemetry: Telemetry
    ) -> Diagnosis:
        evidence = "\n".join(f"- {item}" for item in finding.evidence)
        prompt = "\n".join(
            [
                "You are a senior site reliability engineer performing repository-aware root cause "
                "analysis for a refactoring agent.",
                "",
                f"Repository: {scenario.target}@{scenario.commit}",
                f"Failing symbol: {finding.symbol} in {finding.file_path}",
                f"Failure category: {finding.category}",
                f"Collapse detected after {telemetry.time_to_collapse_s}s under the load scenario {scenario.name}",
                "",
                "Evidence:",
                evidence,
                "",
                "Write a concise analysis and a concrete refactor plan using repository patterns.",
                "Respond exactly in this format:",
                "ANALYSIS:",
                "<markdown analysis>",
                "PROPOSED_CHANGE:",
                "<one sentence describing the code change>",
            ]
        )
        text = self.client.generate(prompt)
        analysis_md, proposed_change = _parse_sections(text)
        if not proposed_change:
            _, proposed_change = FALLBACK_ANALYSIS.get(finding.category, DEFAULT_FALLBACK)
        return Diagnosis(
            model=self.settings.watsonx_model_id,
            analysis_md=analysis_md or self._fallback(finding).analysis_md,
            proposed_change=proposed_change,
        )


def _parse_sections(text: str) -> Tuple[str, str]:
    analysis = ""
    proposed = ""
    if "PROPOSED_CHANGE:" in text:
        head, tail = text.split("PROPOSED_CHANGE:", 1)
        analysis = head.replace("ANALYSIS:", "").strip()
        proposed = tail.strip().split("\n")[0].strip()
    else:
        analysis = text.replace("ANALYSIS:", "").strip()
    return analysis, proposed
