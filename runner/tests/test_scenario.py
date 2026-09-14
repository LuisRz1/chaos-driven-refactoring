from pathlib import Path

from cdr.scenario import list_scenarios, load_scenario

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_load_checkout_scenario():
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    assert scenario.name == "checkout-latency-cascade"
    assert scenario.target == "GoogleCloudPlatform/microservices-demo"
    assert scenario.load.vus == 200
    assert scenario.chaos.fault == "latency"
    assert scenario.thresholds.p95_ms == 500


def test_list_scenarios():
    paths = list_scenarios(SCENARIOS_DIR)
    assert len(paths) >= 2
    assert any("checkout-latency-cascade" in path for path in paths)
