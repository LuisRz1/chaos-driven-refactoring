from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[2]

BLOCKED_MODELS = {
    "meta-llama/llama-3-405b-instruct",
    "mistralai/mistral-medium-2505",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
}


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


@dataclass
class Settings:
    mode: str = field(default_factory=lambda: _env("CDR_MODE", "mock"))
    artifacts_dir: Path = field(
        default_factory=lambda: Path(_env("CDR_ARTIFACTS_DIR", str(REPO_ROOT / "artifacts")))
    )
    watsonx_url: str = field(
        default_factory=lambda: _env("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    )
    watsonx_api_key: str = field(default_factory=lambda: _env("WATSONX_API_KEY"))
    watsonx_project_id: str = field(default_factory=lambda: _env("WATSONX_PROJECT_ID"))
    watsonx_model_id: str = field(
        default_factory=lambda: _env("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
    )
    supabase_url: str = field(default_factory=lambda: _env("SUPABASE_URL"))
    supabase_service_role_key: str = field(
        default_factory=lambda: _env("SUPABASE_SERVICE_ROLE_KEY")
    )
    supabase_schema: str = field(default_factory=lambda: _env("SUPABASE_SCHEMA", "cdr"))
    github_repo: str = field(default_factory=lambda: _env("CDR_GITHUB_REPO"))
    github_token: str = field(default_factory=lambda: _env("GITHUB_TOKEN"))

    @property
    def watsonx_configured(self) -> bool:
        return bool(self.watsonx_api_key and self.watsonx_project_id)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    def safe_summary(self) -> Dict[str, str]:
        return {
            "mode": self.mode,
            "artifacts_dir": str(self.artifacts_dir),
            "watsonx_model_id": self.watsonx_model_id,
            "watsonx_configured": str(self.watsonx_configured),
            "supabase_configured": str(self.supabase_configured),
            "github_repo": self.github_repo or "not set",
        }
