from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .config import BLOCKED_MODELS, Settings

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class WatsonxClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._token: Optional[str] = None

    @property
    def configured(self) -> bool:
        return self.settings.watsonx_configured

    def _access_token(self) -> str:
        if self._token:
            return self._token
        response = httpx.post(
            IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.settings.watsonx_api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        return self._token

    def generate(self, prompt: str, max_new_tokens: int = 700) -> str:
        model_id = self.settings.watsonx_model_id
        if model_id in BLOCKED_MODELS:
            raise ValueError(
                f"model {model_id} is out of scope for this hackathon"
            )
        response = httpx.post(
            "{}/ml/v1/text/generation".format(self.settings.watsonx_url.rstrip("/")),
            params={"version": "2024-05-31"},
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
            json={
                "model_id": model_id,
                "input": prompt,
                "project_id": self.settings.watsonx_project_id,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_new_tokens,
                    "min_new_tokens": 1,
                    "temperature": 0.2,
                },
            },
            timeout=90,
        )
        response.raise_for_status()
        payload: Dict[str, Any] = response.json()
        results = payload.get("results") or []
        if not results:
            raise RuntimeError("watsonx returned no results")
        return results[0].get("generated_text", "").strip()
