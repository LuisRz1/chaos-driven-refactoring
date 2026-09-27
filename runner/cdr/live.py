from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import httpx

from .config import Settings
from .models import Patch, Scenario, Telemetry, TelemetrySample


def _percentile(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return float(ordered[index])


def _parse_time(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _detect_collapse(samples: List[TelemetrySample], scenario: Scenario) -> Optional[float]:
    for sample in samples:
        if sample.t < scenario.load.injection_at_s:
            continue
        if (
            sample.p95 > scenario.thresholds.p95_ms * 3
            or sample.error_rate > scenario.thresholds.collapse_error_rate * 100
        ):
            return float(sample.t)
    return None


def parse_k6_json(path: Path, scenario: Scenario) -> Telemetry:
    points: Dict[str, List[tuple]] = {
        "cdr_checkout_duration": [],
        "cdr_checkout_failed": [],
        "cdr_checkout_requests": [],
    }
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("type") != "Point" or payload.get("metric") not in points:
                continue
            data = payload.get("data") or {}
            try:
                points[payload["metric"]].append(
                    (_parse_time(str(data["time"])), float(data["value"]))
                )
            except (KeyError, TypeError, ValueError):
                continue

    durations = points["cdr_checkout_duration"]
    failures = points["cdr_checkout_failed"]
    requests = points["cdr_checkout_requests"]
    if not durations:
        raise RuntimeError("k6 produced no checkout telemetry points")

    started = min(timestamp for timestamp, _ in durations)
    buckets: Dict[int, Dict[str, List[float]]] = {}
    for metric, values in points.items():
        for timestamp, value in values:
            bucket = int((timestamp - started) // 3) * 3
            buckets.setdefault(bucket, {}).setdefault(metric, []).append(value)

    samples: List[TelemetrySample] = []
    for offset in sorted(buckets):
        bucket = buckets[offset]
        latency = bucket.get("cdr_checkout_duration", [])
        failed = bucket.get("cdr_checkout_failed", [])
        request_points = bucket.get("cdr_checkout_requests", [])
        if not latency:
            continue
        samples.append(
            TelemetrySample(
                t=offset,
                p95=round(_percentile(latency, 0.95), 1),
                p99=round(_percentile(latency, 0.99), 1),
                error_rate=round((sum(failed) / len(failed) * 100) if failed else 0.0, 2),
                rps=round(sum(request_points) / 3.0, 1),
            )
        )

    all_latency = [value for _, value in durations]
    all_failures = [value for _, value in failures]
    elapsed = max(1.0, max(timestamp for timestamp, _ in durations) - started)
    error_rate = (sum(all_failures) / len(all_failures) * 100) if all_failures else 0.0
    p95 = _percentile(all_latency, 0.95)
    p99 = _percentile(all_latency, 0.99)
    collapse = _detect_collapse(samples, scenario)
    latency_ms = scenario.chaos.attributes.get("latency_ms", 0)
    signals = [
        (
            f"Toxiproxy injected {latency_ms:.0f} ms latency on {scenario.chaos.proxy} "
            f"at t={scenario.load.injection_at_s}s"
        ),
        f"checkout p95 reached {p95:.0f} ms under the controlled downstream fault",
        f"checkout error rate reached {error_rate:.1f}% during the experiment",
    ]
    if collapse is not None:
        signals.append(f"injected latency caused a reproducible downstream timeout cascade at t={collapse:.0f}s")

    return Telemetry(
        samples=samples,
        p95_ms=round(p95, 1),
        p99_ms=round(p99, 1),
        error_rate=round(error_rate, 2),
        rps=round(sum(value for _, value in requests) / elapsed, 1),
        time_to_collapse_s=collapse,
        log_signals=signals,
    )


class LiveLab:
    def __init__(self, settings: Settings, run_id: str) -> None:
        self.settings = settings
        self.run_id = run_id
        self.run_dir = settings.artifacts_dir / run_id / "live"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.compose_file = self.repo_root / "infra" / "target" / "docker-compose.yml"
        self.load_script = self.repo_root / "infra" / "load" / "checkout-load.js"
        self.override_file: Optional[Path] = None

    def _binary(self, configured: str, fallback: str) -> str:
        binary = configured or fallback
        resolved = shutil.which(binary)
        if resolved is None:
            raise RuntimeError(f"{fallback} is required for live mode but was not found")
        return resolved

    @property
    def docker(self) -> str:
        return self._binary(self.settings.docker_binary, "docker")

    @property
    def k6(self) -> str:
        return self._binary(self.settings.k6_binary, "k6")

    def _compose_args(self) -> List[str]:
        args = [self.docker, "compose", "-f", str(self.compose_file)]
        if self.override_file is not None:
            args.extend(["-f", str(self.override_file)])
        return args

    def _run(self, command: List[str], cwd: Optional[Path] = None, timeout: int = 600) -> str:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else str(self.repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "command failed").strip()[-800:]
            raise RuntimeError(f"live command failed ({completed.returncode}): {detail}")
        return completed.stdout

    def prepare(self) -> None:
        self._run(self._compose_args() + ["up", "-d", "--remove-orphans"], timeout=900)
        self._wait_for_target()

    def _wait_for_target(self) -> None:
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            try:
                response = httpx.get(self.settings.live_base_url, timeout=3)
                if response.status_code < 500:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(2)
        raise RuntimeError(f"live target did not become ready at {self.settings.live_base_url}")

    def _toxic_url(self, scenario: Scenario) -> str:
        base = self.settings.toxiproxy_url.rstrip("/")
        return f"{base}/proxies/{scenario.chaos.proxy}/toxics/cdr-injected-fault"

    def _clear_toxic(self, scenario: Scenario) -> None:
        try:
            httpx.delete(self._toxic_url(scenario), timeout=5)
        except httpx.HTTPError:
            pass

    def _inject_toxic(self, scenario: Scenario) -> None:
        attributes = scenario.chaos.attributes
        if scenario.chaos.fault == "latency":
            toxic_type = "latency"
            toxic_attributes = {
                "latency": int(attributes.get("latency_ms", 800)),
                "jitter": int(attributes.get("jitter_ms", 0)),
            }
        elif scenario.chaos.fault == "abort":
            toxic_type = "reset_peer"
            toxic_attributes = {"timeout": int(attributes.get("timeout_ms", 0))}
        else:
            raise RuntimeError(f"unsupported live toxic: {scenario.chaos.fault}")
        response = httpx.post(
            self.settings.toxiproxy_url.rstrip("/") + f"/proxies/{scenario.chaos.proxy}/toxics",
            json={
                "name": "cdr-injected-fault",
                "type": toxic_type,
                "stream": "downstream",
                "toxicity": 1.0,
                "attributes": toxic_attributes,
            },
            timeout=10,
        )
        response.raise_for_status()

    def capture(self, scenario: Scenario, label: str) -> Telemetry:
        output_path = self.run_dir / f"k6-{label}.jsonl"
        console_path = self.run_dir / f"k6-{label}.log"
        self._clear_toxic(scenario)
        env = os.environ.copy()
        env.update(
            {
                "BASE_URL": self.settings.live_base_url,
                "CDR_VUS": str(scenario.load.vus),
                "CDR_DURATION_S": str(scenario.load.duration_s),
            }
        )
        process = subprocess.Popen(
            [self.k6, "run", "--out", f"json={output_path}", str(self.load_script)],
            cwd=str(self.repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        try:
            time.sleep(scenario.load.injection_at_s)
            if process.poll() is not None:
                output, _ = process.communicate()
                raise RuntimeError(f"k6 exited before fault injection: {output[-800:]}")
            self._inject_toxic(scenario)
            output, _ = process.communicate(
                timeout=max(90, scenario.load.duration_s - scenario.load.injection_at_s + 60)
            )
        except subprocess.TimeoutExpired as error:
            process.kill()
            output, _ = process.communicate()
            raise RuntimeError(f"k6 timed out: {output[-800:]}") from error
        finally:
            self._clear_toxic(scenario)
        console_path.write_text(output or "", encoding="utf-8")
        if process.returncode != 0:
            raise RuntimeError(
                f"k6 exited with code {process.returncode}: {(output or '')[-800:]}"
            )
        return parse_k6_json(output_path, scenario)

    def deploy_patch(self, workspace: Path, patch: Patch) -> None:
        if patch.source != "bob-shell" or not patch.diff.strip():
            raise RuntimeError("live verification requires a real Bob patch")
        if not any(p.startswith("src/checkoutservice/") for p in patch.files_changed):
            raise RuntimeError("the live checkout scenario requires a checkoutservice patch")
        service_dir = workspace / "src" / "checkoutservice"
        if not (service_dir / "Dockerfile").exists():
            raise RuntimeError("checkoutservice Dockerfile was not found in the cloned repository")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False, encoding="utf-8") as tmp:
            tmp.write(patch.diff)
            patch_file = tmp.name
        try:
            apply_check = subprocess.run(
                ["git", "apply", "--check", patch_file],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if apply_check.returncode == 0:
                self._run(["git", "apply", "--whitespace=fix", patch_file], cwd=workspace, timeout=60)
            else:
                reverse_check = subprocess.run(
                    ["git", "apply", "--reverse", "--check", patch_file],
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                )
                if reverse_check.returncode != 0:
                    detail = (apply_check.stderr or apply_check.stdout or "git apply failed").strip()[-800:]
                    raise RuntimeError(f"patch did not apply cleanly: {detail}")
        finally:
            try:
                Path(patch_file).unlink()
            except OSError:
                pass

        image = f"cdr-checkoutservice:{self.run_id.lower()}"
        self._run([self.docker, "build", "-t", image, "."], cwd=service_dir, timeout=900)
        self.override_file = self.run_dir / "docker-compose.patch.yml"
        self.override_file.write_text(
            f"services:\n  checkoutservice:\n    image: {image}\n",
            encoding="utf-8",
        )
        self._run(
            self._compose_args()
            + ["up", "-d", "--no-deps", "--force-recreate", "checkoutservice"],
            timeout=300,
        )
        self._wait_for_target()
