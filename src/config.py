import os
from typing import Optional


def _secrets_get(key: str) -> Optional[str]:
    if os.environ.get("GROQ_API_KEY"):
        return None
    try:
        import streamlit as st

        if hasattr(st.secrets, "load_if_toml_exists"):
            if not st.secrets.load_if_toml_exists():
                return None
        return st.secrets.get(key)
    except Exception:
        return None


def _get(key: str, default: Optional[str] = None) -> Optional[str]:
    env_value = os.environ.get(key)
    if env_value is not None:
        return env_value
    secrets_value = _secrets_get(key)
    if secrets_value is not None:
        return secrets_value
    return default


_DEFAULT_USER_AGENT = (
    "GhanexAssessmentAgent/1.0 "
    "(https://github.com/nite208/tool-calling-ai-agent; niteshkumawat2331@gmail.com)"
)

GROQ_API_KEY: str = _get("GROQ_API_KEY", "") or ""
USER_AGENT: str = _get("USER_AGENT", _DEFAULT_USER_AGENT) or _DEFAULT_USER_AGENT
GROQ_MODEL: str = _get("GROQ_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b"

MAX_AGENT_STEPS: int = int(_get("MAX_AGENT_STEPS", "10") or "10")
REQUEST_TIMEOUT: int = int(_get("REQUEST_TIMEOUT", "10") or "10")
MAX_TOKENS: int = int(_get("MAX_TOKENS", "1024") or "1024")
TEMPERATURE: float = float(_get("TEMPERATURE", "0.7") or "0.7")
