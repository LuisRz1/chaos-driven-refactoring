import json
from pathlib import Path

import pytest

from cdr.config import Settings
from cdr.live import LiveLab, parse_k6_json
from cdr.models import Patch
from cdr.scenario import load_scenario

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def _point(metric, second, value):
    return {
        "type": "Point",
        "metric": metric,
        "data": {"time": f"2026-09-27T00:00:{second:02d}Z", "value": value},
    }


def test_parse_k6_json_builds_real_telemetry(tmp_path):
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    scenario.load.injection_at_s = 3
    output = tmp_path / "k6.jsonl"
    rows = []
    for second, latency, failed in [(0, 200, 0), (3, 1800, 1), (6, 2100, 1)]:
        rows.extend(
            [
                _point("cdr_checkout_duration", second, latency),
                _point("cdr_checkout_failed", second, failed),
                _point("cdr_checkout_requests", second, 1),
            ]
        )
    output.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    telemetry = parse_k6_json(output, scenario)

    assert telemetry.p95_ms == 2100
    assert telemetry.error_rate == pytest.approx(66.67)
    assert telemetry.time_to_collapse_s == 3
    assert telemetry.rps > 0
    assert any("Toxiproxy injected" in signal for signal in telemetry.log_signals)


def test_parse_k6_json_rejects_empty_output(tmp_path):
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    output = tmp_path / "k6.jsonl"
    output.write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="no checkout telemetry"):
        parse_k6_json(output, scenario)


def test_live_deploy_requires_real_bob_patch(tmp_path):
    settings = Settings()
    settings.artifacts_dir = tmp_path / "artifacts"
    lab = LiveLab(settings, "run-test")
    patch = Patch(
        branch="cdr/fix-test",
        files_changed=["src/checkoutservice/main.go"],
        diff="diff",
        source="template",
    )

    with pytest.raises(RuntimeError, match="real Bob patch"):
        lab.deploy_patch(tmp_path, patch)
