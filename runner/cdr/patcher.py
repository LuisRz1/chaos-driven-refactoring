from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .config import Settings
from .models import Diagnosis, Finding, Patch, Scenario

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

    def build_patch(self, scenario: Scenario, finding: Finding, diagnosis: Diagnosis) -> Patch:
        branch = f"cdr/fix-{slugify(scenario.name)}"
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
                    encoding="utf-8",
                    errors="replace",
                    check=True,
                )
                output = completed.stdout.strip()
            return output.splitlines()[-1] if output else None
        except Exception:
            return None
