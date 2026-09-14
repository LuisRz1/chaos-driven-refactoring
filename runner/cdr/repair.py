from __future__ import annotations

from typing import Optional, Tuple

from .bob_client import BobClient
from .config import Settings
from .diagnoser import _derive_proposed_change, _parse_sections
from .models import Diagnosis, Finding, Patch, Scenario, Telemetry
from .patcher import slugify
from .repo_context import ensure_repo_clone
from .workspace import is_managed_workspace, reset_workspace, workspace_diff, workspace_files

PROMPT_TEMPLATE = "\n".join(
    [
        "You are a senior site reliability engineer working inside this repository clone "
        "({target}@{commit}).",
        "A chaos experiment reproduced a production collapse with this signature:",
        "- Failure category: {category}",
        "- Symptoms: {evidence}",
        "",
        "Task:",
        "1. Read the repository and find where this failure class can originate in THIS codebase.",
        "2. Apply the minimal production-quality fix directly to the relevant source files.",
        "3. Do not create documentation files, do not touch tests, lockfiles or CI config.",
        "4. Do not run builds, installers or test suites.",
        "5. Reply exactly in this format:",
        "ANALYSIS:",
        "<concise markdown analysis of the root cause in this repository>",
        "FILES:",
        "<comma-separated repository-relative paths you changed>",
        "PROPOSED_CHANGE:",
        "<one sentence describing the change you applied>",
    ]
)


class BobRepairer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bob = BobClient(settings)

    @property
    def available(self) -> bool:
        return self.settings.bob_patches and self.bob.available

    def repair(
        self, scenario: Scenario, finding: Finding, telemetry: Telemetry
    ) -> Optional[Tuple[Diagnosis, Patch]]:
        workspace = ensure_repo_clone(self.settings, scenario.target, scenario.commit)
        if workspace is None or not is_managed_workspace(self.settings, workspace):
            return None
        reset_workspace(workspace)

        evidence = " | ".join(finding.evidence[:4])
        prompt = PROMPT_TEMPLATE.format(
            target=scenario.target,
            commit=scenario.commit,
            category=finding.category,
            evidence=evidence,
        )
        result = self.bob.run(
            prompt,
            workspace=workspace,
            mode="agent",
            max_cost=self.settings.bob_patch_max_cost,
        )

        diff = workspace_diff(workspace)
        changed_files = workspace_files(workspace)
        if not changed_files or not diff.strip():
            return None

        analysis_md, _, proposed_change = _parse_sections(result.text)
        if not proposed_change:
            proposed_change = _derive_proposed_change(analysis_md)
        if not proposed_change:
            proposed_change = f"Apply the minimal resilience fix in {changed_files[0]}."
        if not analysis_md:
            analysis_md = result.text.strip() or "Bob applied a minimal resilience fix."

        diagnosis = Diagnosis(
            model="bob-shell",
            analysis_md=analysis_md,
            proposed_change=proposed_change,
            bob_task_id=result.task_id,
            bobcoins=result.bobcoins,
            target_files=changed_files,
        )
        patch = Patch(
            branch=f"cdr/fix-{slugify(scenario.name)}",
            files_changed=changed_files,
            diff=diff,
            source="bob-shell",
            bob_task_id=result.task_id,
            bobcoins=result.bobcoins,
        )
        return diagnosis, patch
