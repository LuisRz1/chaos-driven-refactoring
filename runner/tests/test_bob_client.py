from pathlib import Path

from cdr.bob_client import parse_bob_output
from cdr.classifier import classify
from cdr.config import Settings
from cdr.diagnoser import Diagnoser, _parse_sections
from cdr.scenario import load_scenario
from cdr.telemetry import simulate_telemetry

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_parse_bob_output_extracts_task_and_cost():
    line = (
        '{"type":"result","status":"success","stats":{"task_id":"abc123","session_costs":0.42},'
        '"last_message":"ANALYSIS:\\nroot cause\\nPROPOSED_CHANGE:\\nfix it"}'
    )
    result = parse_bob_output("some log line\n" + line + "\n")
    assert result is not None
    assert result.task_id == "abc123"
    assert result.bobcoins == 0.42
    assert result.status == "success"
    assert "PROPOSED_CHANGE" in result.text


def test_parse_bob_output_returns_none_without_result_line():
    assert parse_bob_output("no json here") is None


def test_parse_sections_with_files_block():
    text = (
        "ANALYSIS:\nroot cause\n"
        "FILES:\nbackend/src/a.py#init_client, backend/src/b.py\n"
        "PROPOSED_CHANGE:\nGuard the dependency call"
    )
    analysis, files, proposed = _parse_sections(text)
    assert analysis == "root cause"
    assert files == ["backend/src/a.py#init_client", "backend/src/b.py"]
    assert proposed == "Guard the dependency call"


def test_parse_sections_without_files_block():
    analysis, files, proposed = _parse_sections("ANALYSIS:\nroot\nPROPOSED_CHANGE:\nfix")
    assert files == []
    assert proposed == "fix"


def test_diagnoser_rules_mode_never_calls_bob(monkeypatch):
    monkeypatch.delenv("BOB_API_KEY", raising=False)
    settings = Settings()
    settings.analyzer = "rules"
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    telemetry = simulate_telemetry(scenario, fixed=False)
    finding = classify(telemetry)
    diagnosis = Diagnoser(settings).diagnose(scenario, finding, telemetry)
    assert diagnosis.model == "rule-based-fallback"
    assert diagnosis.bob_task_id is None
    assert diagnosis.proposed_change


def test_diagnoser_auto_falls_back_without_credentials(monkeypatch):
    monkeypatch.delenv("BOB_API_KEY", raising=False)
    monkeypatch.delenv("WATSONX_API_KEY", raising=False)
    monkeypatch.delenv("WATSONX_PROJECT_ID", raising=False)
    monkeypatch.setattr(
        "cdr.bob_client.BobClient.available", property(lambda self: False)
    )
    settings = Settings()
    settings.analyzer = "auto"
    scenario = load_scenario(SCENARIOS_DIR / "payment-dependency-timeout.yaml")
    telemetry = simulate_telemetry(scenario, fixed=False)
    finding = classify(telemetry)
    diagnosis = Diagnoser(settings).diagnose(scenario, finding, telemetry)
    assert diagnosis.model == "rule-based-fallback"
