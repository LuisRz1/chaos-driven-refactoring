from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

import yaml

from .models import ChaosConfig, LoadConfig, Scenario, Thresholds


def load_scenario(path: Union[str, Path]) -> Scenario:
    raw: Dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    load = LoadConfig(**raw.get("load", {}))
    chaos = ChaosConfig(**raw.get("chaos", {}))
    thresholds = Thresholds(**raw.get("thresholds", {}))
    return Scenario(
        name=raw["name"],
        target=raw["target"],
        commit=str(raw.get("commit", "main")),
        mode=raw.get("mode", "mock"),
        load=load,
        chaos=chaos,
        thresholds=thresholds,
    )


def list_scenarios(directory: Union[str, Path]) -> list:
    return sorted(str(path) for path in Path(directory).glob("*.yaml"))
