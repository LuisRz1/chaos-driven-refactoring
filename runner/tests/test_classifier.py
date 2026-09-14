from pathlib import Path

from cdr.classifier import classify
from cdr.scenario import load_scenario
from cdr.telemetry import simulate_telemetry

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_latency_fault_classified_as_unresilient_dependency():
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    telemetry = simulate_telemetry(scenario, fixed=False)
    finding = classify(telemetry)
    assert finding.category == "unresilient_dependency"
    assert finding.confidence >= 0.86
    assert finding.file_path == "src/checkoutservice/main.go"
    assert any("deadline" in signal for signal in telemetry.log_signals)


def test_abort_fault_classified_as_unresilient_dependency():
    scenario = load_scenario(SCENARIOS_DIR / "payment-dependency-timeout.yaml")
    telemetry = simulate_telemetry(scenario, fixed=False)
    finding = classify(telemetry)
    assert finding.category == "unresilient_dependency"


def test_fixed_run_produces_no_collapse():
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    telemetry = simulate_telemetry(scenario, fixed=True)
    assert telemetry.time_to_collapse_s is None
    assert telemetry.p95_ms < 500
    assert telemetry.error_rate < 5
