import pytest


@pytest.fixture(autouse=True)
def isolate_external_analyzers(monkeypatch):
    monkeypatch.setenv("CDR_ANALYZER", "rules")
    monkeypatch.setenv("CDR_CLONE_REPOS", "0")
    monkeypatch.delenv("BOB_API_KEY", raising=False)
    monkeypatch.delenv("WATSONX_API_KEY", raising=False)
    monkeypatch.delenv("WATSONX_PROJECT_ID", raising=False)
    yield
