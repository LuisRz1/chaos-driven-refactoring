from pathlib import Path

from cdr.classifier import classify
from cdr.config import Settings
from cdr.models import Diagnosis
from cdr.patcher import Patcher, slugify
from cdr.scenario import load_scenario
from cdr.telemetry import simulate_telemetry

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_slugify():
    assert slugify("Checkout Latency Cascade!") == "checkout-latency-cascade"


def test_template_patch_used_when_bob_disabled(tmp_path):
    settings = Settings()
    settings.analyzer = "rules"
    settings.bob_patches = False
    settings.artifacts_dir = tmp_path / "artifacts"
    scenario = load_scenario(SCENARIOS_DIR / "checkout-latency-cascade.yaml")
    telemetry = simulate_telemetry(scenario, fixed=False)
    finding = classify(telemetry)
    diagnosis = Diagnosis(
        model="bob-shell",
        analysis_md="## Analysis\n\nroot cause",
        proposed_change="Add a deadline",
    )
    patch = Patcher(settings).build_patch(scenario, finding, diagnosis)
    assert patch.source == "template"
    assert patch.branch == "cdr/fix-checkout-latency-cascade"
    assert patch.files_changed == ["src/checkoutservice/main.go"]
    assert "Add a deadline" in patch.diff
    assert patch.bob_task_id is None
