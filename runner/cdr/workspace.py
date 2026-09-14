from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from .config import Settings


def managed_root(settings: Settings) -> Path:
    return (settings.artifacts_dir / "repos").resolve()


def is_managed_workspace(settings: Settings, workspace: Path) -> bool:
    try:
        Path(workspace).resolve().relative_to(managed_root(settings))
        return True
    except ValueError:
        return False


def git(args: List[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def reset_workspace(workspace: Path) -> None:
    git(["reset", "--hard"], workspace)
    git(["clean", "-fd"], workspace)


CODE_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".sql", ".cs", ".php",
    ".kt", ".rs", ".dart", ".gd", ".astro", ".c", ".cpp", ".h", ".sh", ".vue", ".svelte",
)


def workspace_diff(workspace: Path) -> str:
    git(["add", "-u"], workspace)
    untracked = git(["ls-files", "--others", "--exclude-standard"], workspace, timeout=60)
    new_sources = [
        line.strip()
        for line in untracked.stdout.splitlines()
        if line.strip().lower().endswith(CODE_EXTENSIONS)
    ]
    if new_sources:
        git(["add", "--"] + new_sources, workspace)
    completed = git(["-c", "core.quotepath=false", "diff", "--cached", "--no-color"], workspace)
    return completed.stdout


def workspace_files(workspace: Path) -> List[str]:
    completed = git(["diff", "--cached", "--name-only"], workspace)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def tracked_files(workspace: Path) -> List[str]:
    completed = git(["ls-files"], workspace, timeout=60)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]
