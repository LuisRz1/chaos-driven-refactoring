from pathlib import Path

from cdr.config import Settings
from cdr.queue import SupabaseQueue

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def make_queue() -> SupabaseQueue:
    settings = Settings()
    return SupabaseQueue(settings, scenarios_dir=SCENARIOS_DIR)


def test_scenario_for_known_name_loads_yaml_and_applies_row_fields():
    queue = make_queue()
    row = {
        "scenario_name": "checkout-latency-cascade",
        "target_repo": "owner/repo",
        "commit_sha": "abc123",
        "mode": "live",
    }
    scenario = queue.scenario_for(row)
    assert scenario.target == "owner/repo"
    assert scenario.commit == "abc123"
    assert scenario.mode == "live"
    assert scenario.load.vus == 200


def test_scenario_for_unknown_name_returns_default_with_row_fields():
    queue = make_queue()
    row = {
        "scenario_name": "no-such-scenario",
        "target_repo": "owner/repo",
        "commit_sha": "abc123",
        "mode": "live",
    }
    scenario = queue.scenario_for(row)
    assert scenario.target == "owner/repo"
    assert scenario.commit == "abc123"
    assert scenario.mode == "live"
    assert scenario.thresholds.p95_ms == 500
