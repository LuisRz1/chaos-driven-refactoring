from pathlib import Path

from cdr.config import Settings
from cdr.pipeline import Pipeline
from cdr.scenario import load_scenario
from cdr.sinks import build_sinks, emit_all

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def make_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.artifacts_dir = tmp_path / "artifacts"
    return settings


def test_pipeline_end_to_end_mock(tmp_path):
    settings = make_settings(tmp_path)
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    result = Pipeline(settings).run(scenario, mode="mock")

    assert result.status == "completed"
    assert result.collapse_detected is True
    assert len(result.phases) == 4
    assert result.finding.category == "unresilient_dependency"
    assert result.verification.stable is True
    assert result.summary["p95_before_ms"] > result.summary["p95_after_ms"]
    assert result.summary["stable_after_fix"] is True
    assert result.patch.branch == "cdr/fix-checkout-latency-cascade"
    assert "Proposed change" in result.patch.diff


def test_pipeline_writes_json_and_markdown_artifacts(tmp_path):
    settings = make_settings(tmp_path)
    scenario = load_scenario(SCENARIOS_DIR / "payment-dependency-timeout.yaml")
    result = Pipeline(settings).run(scenario, mode="mock")
    emit_all(build_sinks("json", settings), result)

    run_dir = settings.artifacts_dir / result.run_id
    assert (run_dir / "run.json").exists()
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "Before vs after" in report
    assert "Root cause" in report
    assert "Verification" in report
