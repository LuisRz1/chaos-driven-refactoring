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
        "({target}@{commit}). This is a fully automated pipeline: there is no human to answer "
        "questions, so never ask for clarification and never stop to write a plan file.",
        "A chaos experiment reproduced a production collapse with this signature:",
        "- Failure category: {category}",
        "- Symptoms: {evidence}",
        "- Faulted dependency: {dependency} ({fault}, {attributes})",
        "- Checkout p95 budget: {p95_ms} ms",
        "- Causal source location: {file_path}::{symbol}",
        "",
        "Do this now, in this session:",
        "1. Read at most 6 source files around {file_path} to confirm the failure path.",
        "2. Immediately apply the minimal production-quality fix in {file_path}, editing at most "
        "3 source files total.",
        "3. Do not create documentation files or plan files, do not touch tests, lockfiles or CI.",
        "4. Do not run builds, installers or test suites.",
        "5. Do not edit Kubernetes manifests, deployment configuration or infrastructure files.",
        "6. Preserve mandatory checkout operations and successful responses; degrade only the "
        "faulted optional dependency when the code shows that is safe.",
        "7. After the edits are saved, reply exactly in this format:",
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
            dependency=scenario.chaos.proxy,
            fault=scenario.chaos.fault,
            attributes=scenario.chaos.attributes,
            p95_ms=scenario.thresholds.p95_ms,
            file_path=finding.file_path,
            symbol=finding.symbol,
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
        if len(changed_files) > 3 or finding.file_path not in changed_files:
            reset_workspace(workspace)
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
