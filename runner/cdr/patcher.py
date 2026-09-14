from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .bob_client import BobClient
from .config import Settings
from .models import Diagnosis, Finding, Patch, Scenario
from .repo_context import ensure_repo_clone

DIFF_TEMPLATES = {
    "unresilient_dependency": "\n".join(
        [
            "--- a/src/checkoutservice/main.go",
            "+++ b/src/checkoutservice/main.go",
            "@@ -184,9 +184,16 @@ func (cs *checkoutService) PlaceOrder(ctx context.Context, req *pb.PlaceOrderReq) (*pb.PlaceOrderResp, error) {",  # noqa: E501
            "-\tresp, err := cs.paymentSvc.Charge(ctx, &pb.ChargeRequest{",
            "+\tpayCtx, cancel := context.WithTimeout(ctx, 400*time.Millisecond)",
            "+\tdefer cancel()",
            "+",
            "+\tresp, err := cs.paymentBreaker.Execute(func() (any, error) {",
            "+\t\treturn cs.paymentSvc.Charge(payCtx, &pb.ChargeRequest{",
            " \t\t\tAmount: &pb.Money{CurrencyCode: req.GetCurrencyCode(), Units: total.Units},",
            " \t\t\tCreditCard: req.GetCreditCard(),",
            "-\t})",
            "+\t\t})",
            "+\t})",
            " \tif err != nil {",
            "-\t\treturn nil, status.Errorf(codes.Internal, \"payment failed: %v\", err)",
            "+\t\treturn nil, status.Errorf(codes.Unavailable, \"payment unavailable: %v\", err)",
            " \t}",
        ]
    ),
    "concurrency": "\n".join(
        [
            "--- a/src/cartservice/cartstore.go",
            "+++ b/src/cartservice/cartstore.go",
            "@@ -41,7 +41,10 @@ func (cs *cartStore) AddItem(ctx context.Context, userID, item *pb.CartItem) error {",
            "-\tcs.mu.Lock()",
            "-\tdefer cs.mu.Unlock()",
            "-\tcs.carts[userID] = append(cs.carts[userID], item)",
            "+\tshard := cs.shards[fnv32(userID)%uint32(len(cs.shards))]",
            "+\tshard.mu.Lock()",
            "+\tdefer shard.mu.Unlock()",
            "+\tshard.carts[userID] = append(shard.carts[userID], item)",
            "+\tcs.metrics.itemAdded.Add(1)",
        ]
    ),
    "memory_leak": "\n".join(
        [
            "--- a/src/recommendationservice/server.py",
            "+++ b/src/recommendationservice/server.py",
            "@@ -58,6 +58,8 @@ class RecommendationService:",
            "     def get_recommendations(self, request, context):",
            "         products = self._fetch_products()",
            "+\t\tself._product_cache = LRUCache(maxsize=2048, ttl_s=120)",
            "         response = self._rank(products[:5])",
            " \t\treturn response",
        ]
    ),
    "db_saturation": "\n".join(
        [
            "--- a/src/productcatalogservice/server.go",
            "+++ b/src/productcatalogservice/server.go",
            "@@ -93,8 +93,12 @@ func (p *productCatalog) ListProducts(ctx context.Context, _ *pb.Empty) (*pb.ListProductsResponse, error) {",  # noqa: E501
            "-\tfor _, id := range p.catalogIDs {",
            "-\t\tproduct, err := p.db.QueryRow(ctx, \"SELECT * FROM products WHERE id = $1\", id)",
            "+\trows, err := p.db.Query(ctx, \"SELECT * FROM products WHERE id = ANY($1)\", p.catalogIDs)",
            "+\tif err != nil {",
            "+\t\treturn nil, err",
            "+\t}",
            "+\tdefer rows.Close()",
            "+\tfor rows.Next() {",
            " \t\t// accumulate products",
            " \t}",
        ]
    ),
}

FILE_TARGETS = {
    "unresilient_dependency": ["src/checkoutservice/main.go"],
    "concurrency": ["src/cartservice/cartstore.go"],
    "memory_leak": ["src/recommendationservice/server.py"],
    "db_saturation": ["src/productcatalogservice/server.go"],
}


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class Patcher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bob = BobClient(settings)

    def build_patch(self, scenario: Scenario, finding: Finding, diagnosis: Diagnosis) -> Patch:
        branch = f"cdr/fix-{slugify(scenario.name)}"
        if self.settings.bob_patches and self.bob.available:
            try:
                patch = self._build_with_bob(branch, scenario, finding, diagnosis)
                if patch is not None:
                    return patch
            except Exception:
                pass
        return self._template_patch(branch, finding, diagnosis)

    def _template_patch(self, branch: str, finding: Finding, diagnosis: Diagnosis) -> Patch:
        diff = DIFF_TEMPLATES.get(finding.category, "")
        files_changed = FILE_TARGETS.get(finding.category, [])
        if not diff:
            diff = "--- (manual patch required)\n+++ (manual patch required)\n"
        header = f"# Proposed change: {diagnosis.proposed_change}\n"
        return Patch(
            branch=branch,
            files_changed=list(files_changed),
            diff=header + diff,
            source="template",
        )

    def _build_with_bob(
        self, branch: str, scenario: Scenario, finding: Finding, diagnosis: Diagnosis
    ) -> Optional[Patch]:
        workspace = ensure_repo_clone(self.settings, scenario.target, scenario.commit)
        if workspace is None or not self._is_managed_workspace(workspace):
            return None
        self._reset_workspace(workspace)
        prompt = "\n".join(
            [
                "You are applying a verified refactoring in this repository clone "
                f"({scenario.target}@{scenario.commit}).",
                "A chaos experiment reproduced a production collapse.",
                f"Failure category: {finding.category}",
                f"Root cause: {finding.root_cause}",
                f"Concrete change to apply: {diagnosis.proposed_change}",
                "",
                "Rules:",
                "- Read the relevant source files, then edit them directly in this workspace.",
                "- Apply the minimal production-quality change; keep the existing code style.",
                "- Do not create documentation files, do not touch tests, lockfiles or CI config.",
                "- Do not run builds, installers or test suites.",
                "- When done, reply with a single line: DONE <comma-separated list of changed files>",
            ]
        )
        result = self.bob.run(
            prompt,
            workspace=workspace,
            mode="agent",
            max_cost=self.settings.bob_patch_max_cost,
        )
        diff = self._workspace_diff(workspace)
        if not diff.strip():
            return None
        files = self._workspace_files(workspace)
        return Patch(
            branch=branch,
            files_changed=files or [finding.file_path],
            diff=diff,
            source="bob-shell",
            bob_task_id=result.task_id,
            bobcoins=result.bobcoins,
        )

    def _managed_root(self) -> Path:
        return (self.settings.artifacts_dir / "repos").resolve()

    def _is_managed_workspace(self, workspace: Path) -> bool:
        try:
            workspace.resolve().relative_to(self._managed_root())
            return True
        except ValueError:
            return False

    def _git(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=120,
        )

    def _reset_workspace(self, workspace: Path) -> None:
        self._git(["reset", "--hard"], workspace)
        self._git(["clean", "-fd"], workspace)

    def _workspace_diff(self, workspace: Path) -> str:
        self._git(["add", "-A"], workspace)
        completed = self._git(
            ["-c", "core.quotepath=false", "diff", "--cached", "--no-color"], workspace
        )
        return completed.stdout

    def _workspace_files(self, workspace: Path) -> List[str]:
        completed = self._git(["diff", "--cached", "--name-only"], workspace)
        return [line.strip() for line in completed.stdout.splitlines() if line.strip()]

    def create_pull_request(self, patch: Patch, repo_dir: Optional[Path]) -> Optional[str]:
        if repo_dir is None or not self.settings.github_repo:
            return None
        if not Path(repo_dir).exists():
            return None
        try:
            patch_file = Path(repo_dir) / ".cdr" / "patch.diff"
            patch_file.parent.mkdir(parents=True, exist_ok=True)
            patch_file.write_text(patch.diff, encoding="utf-8")
            commands: List[List[str]] = [
                ["git", "checkout", "-b", patch.branch],
                ["git", "apply", "--3way", str(patch_file)],
                ["git", "add", "-A"],
                ["git", "commit", "-m", "fix: resilient dependency handling under chaos load"],
                ["git", "push", "-u", "origin", patch.branch],
                ["gh", "pr", "create", "--fill"],
            ]
            output = ""
            for command in commands:
                completed = subprocess.run(
                    command,
                    cwd=str(repo_dir),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                output = completed.stdout.strip()
            return output.splitlines()[-1] if output else None
        except Exception:
            return None
