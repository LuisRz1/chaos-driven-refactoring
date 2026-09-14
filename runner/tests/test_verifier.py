from pathlib import Path

from cdr.scenario import load_scenario
from cdr.telemetry import simulate_telemetry
from cdr.verifier import verify

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_verify_reports_improvements_and_stability():
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    before = simulate_telemetry(scenario, fixed=False)
    after = simulate_telemetry(scenario, fixed=True)
    verification = verify(before, after, scenario)
    assert verification.stable is True
    assert verification.improvement_pct["p95"] > 80
    assert verification.improvement_pct["error_rate"] > 80
    assert verification.improvement_pct["collapse"] == 100.0
    assert verification.after.time_to_collapse_s is None
