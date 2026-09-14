from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .config import Settings
from .pipeline import Pipeline
from .progress import SupabaseProgress
from .queue import SupabaseQueue
from .scenario import list_scenarios, load_scenario
from .sinks import StdoutSink, SupabaseSink, build_sinks, emit_all

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

    watch_parser = subparsers.add_parser(
        "watch",
        help="poll Supabase for queued repository analyses and execute them",
    )
    watch_parser.add_argument("--interval", type=int, default=5, help="polling interval in seconds")
    watch_parser.add_argument("--mode", choices=["mock", "live"], default=None)
    watch_parser.add_argument("--once", action="store_true", help="process one queued run and exit")
    watch_parser.add_argument(
        "--pace",
        type=float,
        default=0.0,
        help="seconds to pause between phases (useful for live demos)",
    )

    subparsers.add_parser("doctor", help="print effective configuration without secrets")

    return parser


def _watch(args, settings: Settings) -> int:
    if not settings.supabase_configured:
        print("[cdr] Supabase is not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")
        return 1
    queue = SupabaseQueue(settings)
    sink = SupabaseSink(settings)
    progress = SupabaseProgress(settings)
    stdout = StdoutSink()
    print(f"[cdr] watching for queued runs every {args.interval}s")
    while True:
        row = queue.claim_next()
        if row is None:
            if args.once:
                print("[cdr] no queued runs")
                return 0
            time.sleep(args.interval)
            continue
        run_id = row["id"]
        target = row.get("target_repo")
        print(f"[cdr] claimed {run_id} ({target})")
        progress.start(run_id, str(target))

        def on_progress(stage, payload, current_run=run_id):
            progress.handle(current_run, stage, payload)
            if args.pace > 0:
                time.sleep(args.pace)

        try:
            scenario = queue.scenario_for(row)
            result = Pipeline(settings).run(
                scenario,
                mode=args.mode or row.get("mode"),
                run_id=run_id,
                on_progress=on_progress,
            )
            stdout.emit(result)
            sink.emit_update(result)
        except Exception as error:
            queue.mark_failed(run_id, str(error))
            print(f"[cdr] run {run_id} failed: {error}")
        if args.once:
            return 0


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

    if args.command == "watch":
        return _watch(args, settings)

    scenario = load_scenario(args.scenario)
    pipeline = Pipeline(settings)
    result = pipeline.run(scenario, mode=args.mode, create_pr=args.create_pr)
    emit_all(build_sinks(args.sink, settings), result)
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
