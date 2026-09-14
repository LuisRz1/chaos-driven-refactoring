from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from .config import Settings


def _run_git(args, cwd: Optional[Path] = None, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def ensure_repo_clone(settings: Settings, repo: str, commit: str) -> Optional[Path]:
    if not settings.clone_repos:
        return None
    if "/" not in repo or repo.startswith("unknown"):
        return None
    owner, _, name = repo.partition("/")
    if not owner or not name:
        return None

    dest = settings.artifacts_dir / "repos" / f"{owner}-{name}"
    try:
        if not (dest / ".git").exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            clone = _run_git(
                ["clone", "--depth", "50", f"https://github.com/{repo}.git", str(dest)],
                timeout=240,
            )
            if clone.returncode != 0:
                return None
        if commit and commit not in ("main", "master", "HEAD"):
            _run_git(["checkout", "--force", commit], cwd=dest, timeout=90)
        return dest
    except Exception:
        return None
