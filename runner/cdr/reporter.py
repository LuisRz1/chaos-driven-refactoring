from __future__ import annotations

import json
from pathlib import Path

from .models import RunResult


def render_markdown(result: RunResult) -> str:
    summary = result.summary
    lines = [
        f"# CDR run report — {result.scenario_name}",
        "",
        f"- Run id: `{result.run_id}`",
        f"- Target: `{result.target_repo}@{result.commit_sha}`",
        f"- Mode: {result.mode}",
        f"- Status: {result.status}",
        f"- Collapse detected: {result.collapse_detected}",
        "",
        "## Before vs after (identical chaos scenario)",
        "",
        "| Metric | Before fix | After fix | Improvement |",
        "| --- | --- | --- | --- |",
        "| p95 latency | {} ms | {} ms | -{}% |".format(
            summary.get("p95_before_ms"),
            summary.get("p95_after_ms"),
            result.verification.improvement_pct.get("p95"),
        ),
        "| p99 latency | {} ms | {} ms | -{}% |".format(
            summary.get("p99_before_ms"),
            summary.get("p99_after_ms"),
            result.verification.improvement_pct.get("p99"),
        ),
        "| error rate | {}% | {}% | -{}% |".format(
            summary.get("error_rate_before"),
            summary.get("error_rate_after"),
            result.verification.improvement_pct.get("error_rate"),
        ),
        "| time to collapse | {} s | none | -100% |".format(
            summary.get("time_to_collapse_s")
        ),
        "",
        "## Root cause",
        "",
        f"- Category: **{result.finding.category}** (confidence {round(result.finding.confidence * 100)})",
        f"- Location: `{result.finding.file_path}` `{result.finding.symbol}`",
        "",
        result.finding.root_cause,
        "",
        "## Diagnosis",
        "",
        result.diagnosis.analysis_md,
        "",
        "## Proposed change",
        "",
        result.diagnosis.proposed_change,
        "",
        "## Verification",
        "",
        f"Stable after fix: **{result.verification.stable}**",
        "",
        "## Reproduction",
        "",
        "```bash",
        "cd runner",
        f"python -m cdr run --scenario scenarios/{result.scenario_name}.yaml --mode {result.mode}",
        "```",
    ]
    return "\n".join(lines) + "\n"


def write_report(result: RunResult, artifacts_dir: Path) -> Path:
    run_dir = artifacts_dir / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(
        json.dumps(result.to_dict(), indent=2), encoding="utf-8"
    )
    report_path = run_dir / "report.md"
    report_path.write_text(render_markdown(result), encoding="utf-8")
    return report_path
