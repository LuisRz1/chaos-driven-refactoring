from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import Settings


@dataclass
class BobResult:
    text: str
    task_id: Optional[str]
    bobcoins: Optional[float]
    status: str


def parse_bob_output(stdout: str) -> Optional[BobResult]:
    result_line = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith('{"type":"result"'):
            result_line = stripped
    if result_line is None:
        return None
    try:
        payload = json.loads(result_line)
    except json.JSONDecodeError:
        return None
    stats = payload.get("stats") or {}
    return BobResult(
        text=str(payload.get("last_message") or "").strip(),
        task_id=stats.get("task_id"),
        bobcoins=stats.get("session_costs"),
        status=str(payload.get("status") or "unknown"),
    )


class BobClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def api_key(self) -> str:
        key = self.settings.bob_api_key.strip()
        if key:
            return key
        key_file = Path.home() / ".cdr" / "bob-api-key.txt"
        if key_file.exists():
            return key_file.read_text(encoding="utf-8").strip()
        return ""

    @property
    def binary(self) -> Optional[str]:
        return shutil.which(self.settings.bob_binary or "bob")

    @property
    def available(self) -> bool:
        return bool(self.api_key) and self.binary is not None

    def run(
        self,
        prompt: str,
        workspace: Optional[Path] = None,
        mode: str = "plan",
        max_cost: Optional[float] = None,
    ) -> BobResult:
        binary = self.binary
        if not binary:
            raise RuntimeError("Bob Shell binary not found in PATH")
        if not self.api_key:
            raise RuntimeError("BOB_API_KEY is not configured")

        env = os.environ.copy()
        env["BOB_API_KEY"] = self.api_key
        args = [
            binary,
            "run",
            "--trust",
            "--accept-license",
            "--format",
            "json",
            "--mode",
            mode,
            "--max-cost",
            str(max_cost if max_cost is not None else self.settings.bob_max_cost),
            prompt,
        ]
        command = ["cmd", "/c"] + args if os.name == "nt" else args
        cwd = str(workspace) if workspace else str(Path.cwd())

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.settings.bob_timeout_s,
            cwd=cwd,
            env=env,
        )
        result = parse_bob_output(completed.stdout)
        if result is None or not result.text:
            stderr = (completed.stderr or "").strip()[:300]
            raise RuntimeError(f"Bob Shell returned no result (rc={completed.returncode}): {stderr}")
        return result
