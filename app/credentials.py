import os
from pathlib import Path

from dotenv import dotenv_values
from streamlit.errors import StreamlitSecretNotFoundError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_credential(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        import streamlit as st

        value = str(st.secrets[name]).strip()
    except (KeyError, StreamlitSecretNotFoundError):
        value = ""
    if value:
        return value

    env_file_value = dotenv_values(PROJECT_ROOT / ".env").get(name)
    value = str(env_file_value or "").strip()
    return value or None
