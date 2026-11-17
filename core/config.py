"""환경 설정 로드.

읽는 순서: Streamlit Secrets(배포) → .env / 환경 변수(로컬).
같은 코드가 로컬과 Streamlit Community Cloud에서 모두 동작하도록 한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_MODEL = "gpt-6.1-sol"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# 프로젝트 루트의 .env만 읽는다.
# load_dotenv()를 경로 없이 호출하면 상위 폴더(예: 사용자 홈)까지 올라가며 .env를 찾아
# 다른 프로젝트의 키를 쓰게 되므로 반드시 경로를 지정한다.
load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str

    @property
    def has_api_key(self) -> bool:
        return bool(self.openai_api_key)


def _from_secrets(key: str) -> str | None:
    """st.secrets에서 값을 읽는다. secrets.toml이 없거나 키가 없으면 None."""
    try:
        import streamlit as st

        value = st.secrets.get(key)
    except Exception:  # secrets 파일이 없으면 Streamlit이 예외를 던진다
        return None
    return str(value).strip() if value else None


def _get(key: str) -> str | None:
    value = _from_secrets(key)
    if value:
        return value
    env_value = os.getenv(key, "").strip()
    return env_value or None


def get_settings() -> Settings:
    """현재 실행 환경의 설정을 반환한다."""
    return Settings(
        openai_api_key=_get("OPENAI_API_KEY"),
        openai_model=_get("OPENAI_MODEL") or DEFAULT_MODEL,
    )
