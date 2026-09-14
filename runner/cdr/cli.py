from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Settings
from .pipeline import Pipeline
from .scenario import list_scenarios, load_scenario
from .sinks import build_sinks, emit_all

DEFAULT_SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cdr",
        description=(
            "Chaos-Driven Refactoring runner: inject chaos, classify failures, "
            "generate and verify refactor patches."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="execute a chaos scenario end to end")
    run_parser.add_argument("--scenario", required=True, help="path to a scenario YAML file")
    run_parser.add_argument("--mode", choices=["mock", "live"], default=None)
    run_parser.add_argument(
        "--sink",
        choices=["stdout", "json", "supabase", "all"],
        default="all",
        help="where to publish the run result",
    )
    run_parser.add_argument(
        "--create-pr",
        action="store_true",
        help="attempt to open a pull request with the generated patch (requires a cloned target repo)",
    )

    list_parser = subparsers.add_parser("list-scenarios", help="list available scenarios")
    list_parser.add_argument("--dir", default=str(DEFAULT_SCENARIOS_DIR))

    subparsers.add_parser("doctor", help="print effective configuration without secrets")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings()

    if args.command == "list-scenarios":
        for path in list_scenarios(args.dir):
            print(path)
        return 0

    if args.command == "doctor":
        for key, value in settings.safe_summary().items():
            print(f"{key}: {value}")
        return 0

    scenario = load_scenario(args.scenario)
    pipeline = Pipeline(settings)
    result = pipeline.run(scenario, mode=args.mode, create_pr=args.create_pr)
    emit_all(build_sinks(args.sink, settings), result)
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
