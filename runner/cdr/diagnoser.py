from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from .bob_client import BobClient
from .config import Settings
from .models import Diagnosis, Finding, Scenario, Telemetry
from .repo_context import ensure_repo_clone
from .watsonx import WatsonxClient

FILE_EXTENSIONS = (
    "py|js|ts|tsx|jsx|go|java|rb|sql|yaml|yml|json|cs|php|kt|rs|dart|gd|astro|c|cpp|h|sh"
)
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
BACKTICK_PATH_RE = re.compile(
    r"`([A-Za-z0-9_./-]+\.(?:" + FILE_EXTENSIONS + r"))`"
)
PATH_RE = re.compile(r"\b([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:" + FILE_EXTENSIONS + r"))\b")

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
        self.bob = BobClient(settings)

    def diagnose(
        self,
        scenario: Scenario,
        finding: Finding,
        telemetry: Telemetry,
        exclude_bob: bool = False,
    ) -> Diagnosis:
        for source in self._sources(exclude_bob):
            try:
                if source == "bob" and self.bob.available:
                    return self._diagnose_with_bob(scenario, finding, telemetry)
                if source == "watsonx" and self.client.configured:
                    return self._diagnose_with_watsonx(scenario, finding, telemetry)
            except Exception:
                continue
        return self._fallback(finding)

    def _sources(self, exclude_bob: bool = False):
        configured = (self.settings.analyzer or "auto").lower()
        if configured in ("bob", "watsonx", "rules"):
            return [configured]
        if exclude_bob:
            return ["watsonx", "rules"]
        return ["bob", "watsonx", "rules"]

    def _fallback(self, finding: Finding) -> Diagnosis:
        analysis, proposed = FALLBACK_ANALYSIS.get(finding.category, DEFAULT_FALLBACK)
        return Diagnosis(
            model="rule-based-fallback",
            analysis_md=analysis,
            proposed_change=proposed,
        )

    def _build_prompt(
        self, scenario: Scenario, finding: Finding, telemetry: Telemetry, grounded: bool
    ) -> str:
        evidence = "\n".join(f"- {item}" for item in finding.evidence)
        lines = [
            "You are a senior site reliability engineer performing repository-aware root cause "
            "analysis for a refactoring agent.",
            "",
            f"Repository: {scenario.target}@{scenario.commit}",
            f"Failing symbol: {finding.symbol} in {finding.file_path}",
            f"Failure category: {finding.category}",
            f"Collapse detected after {telemetry.time_to_collapse_s}s under the chaos scenario "
            f"{scenario.name}.",
            "",
            "Evidence:",
            evidence,
            "",
        ]
        if grounded:
            lines.append(
                f"Read the repository source (start with {finding.file_path}) and ground the "
                "analysis in the actual code, citing files or symbols you inspected."
            )
        else:
            lines.append("Base the analysis on the evidence and standard resilience patterns.")
        lines.extend(
            [
                "",
                "Respond exactly in this format:",
                "ANALYSIS:",
                "<concise markdown analysis>",
                "FILES:",
                "<comma-separated repository-relative paths that must change, use path#symbol when known>",
                "PROPOSED_CHANGE:",
                "<one sentence describing the concrete code change>",
            ]
        )
        return "\n".join(lines)

    def _diagnose_with_bob(
        self, scenario: Scenario, finding: Finding, telemetry: Telemetry
    ) -> Diagnosis:
        workspace = ensure_repo_clone(self.settings, scenario.target, scenario.commit)
        if workspace is None:
            workspace = self.settings.artifacts_dir / "bob-workspace"
            workspace.mkdir(parents=True, exist_ok=True)
        prompt = self._build_prompt(
            scenario, finding, telemetry, grounded=workspace is not None
        )
        result = self.bob.run(prompt, workspace=workspace, mode="plan")
        analysis_md, target_files, proposed_change = _parse_sections(result.text)
        if not analysis_md and not proposed_change:
            raise RuntimeError("Bob Shell returned an unparseable analysis")
        if not target_files:
            target_files = _extract_repo_files(result.text, workspace)
        if not proposed_change:
            proposed_change = _derive_proposed_change(analysis_md)
        if not proposed_change:
            _, proposed_change = FALLBACK_ANALYSIS.get(finding.category, DEFAULT_FALLBACK)
        return Diagnosis(
            model="bob-shell",
            analysis_md=analysis_md or self._fallback(finding).analysis_md,
            proposed_change=proposed_change,
            bob_task_id=result.task_id,
            bobcoins=result.bobcoins,
            target_files=target_files,
        )

    def _diagnose_with_watsonx(
        self, scenario: Scenario, finding: Finding, telemetry: Telemetry
    ) -> Diagnosis:
        prompt = self._build_prompt(scenario, finding, telemetry, grounded=False)
        text = self.client.generate(prompt)
        analysis_md, target_files, proposed_change = _parse_sections(text)
        if not proposed_change:
            _, proposed_change = FALLBACK_ANALYSIS.get(finding.category, DEFAULT_FALLBACK)
        return Diagnosis(
            model=self.settings.watsonx_model_id,
            analysis_md=analysis_md or self._fallback(finding).analysis_md,
            proposed_change=proposed_change,
            target_files=target_files,
        )


def _parse_files(block: str) -> list:
    cleaned = block.replace("\n", ",").replace(";", ",")
    files = [item.strip().strip("`") for item in cleaned.split(",")]
    return [item for item in files if item][:5]


def _extract_repo_files(text: str, workspace: Path) -> List[str]:
    candidates: List[str] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        candidates.append(match.group(1))
    for match in BACKTICK_PATH_RE.finditer(text):
        candidates.append(match.group(1))
    for match in PATH_RE.finditer(text):
        candidates.append(match.group(1))

    found: List[str] = []
    for candidate in candidates:
        candidate = candidate.split("#")[0].strip().lstrip("./")
        if candidate.startswith(("http://", "https://", "/")):
            continue
        path = workspace / candidate
        if path.exists() and path.is_file() and candidate not in found:
            found.append(candidate)
        if len(found) >= 5:
            break
    return found


def _derive_proposed_change(analysis: str) -> str:
    if not analysis:
        return ""
    for keyword in ("fix", "refactor", "recommend", "change", "plan"):
        pattern = re.compile(
            r"#+[^\n]*" + keyword + r"[^\n]*\n+([^\n#|`>]+)", re.IGNORECASE
        )
        match = pattern.search(analysis)
        if match:
            line = match.group(1).strip()
            if len(line) > 20:
                return line[:300]
    for line in analysis.splitlines():
        stripped = line.strip()
        if len(stripped) < 40 or stripped.startswith(("#", "|", "```", ">", "-", "*")):
            continue
        if stripped.lower().startswith(("let me", "i now", "here is", "sure,", "sure!")):
            continue
        return stripped[:300]
    return ""


def _parse_sections(text: str) -> Tuple[str, list, str]:
    analysis = ""
    target_files: list = []
    proposed = ""
    body = text
    if "FILES:" in body:
        head, tail = body.split("FILES:", 1)
        body = head
        files_block, _, after = tail.partition("PROPOSED_CHANGE:")
        target_files = _parse_files(files_block)
        proposed = after.strip().split("\n")[0].strip() if after else ""
    if "PROPOSED_CHANGE:" in body:
        head, tail = body.split("PROPOSED_CHANGE:", 1)
        analysis = head.replace("ANALYSIS:", "").strip()
        proposed = proposed or tail.strip().split("\n")[0].strip()
    else:
        analysis = body.replace("ANALYSIS:", "").strip()
    return analysis, target_files, proposed
