from pathlib import Path

from core import config


def test_env_file_is_project_root_only():
    """상위 폴더의 .env가 아니라 프로젝트 루트의 .env만 읽어야 한다."""
    project_root = Path(__file__).resolve().parent.parent
    assert config.ENV_FILE == project_root / ".env"


def test_default_model_when_env_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr(config, "_from_secrets", lambda key: None)
    assert config.get_settings().openai_model == "gpt-6.1-sol"


def test_secrets_take_priority_over_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    monkeypatch.setattr(config, "_from_secrets", lambda key: "from-secrets" if key == "OPENAI_API_KEY" else None)
    assert config.get_settings().openai_api_key == "from-secrets"
