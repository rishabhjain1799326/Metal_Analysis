import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("FRED_API_KEY")

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_series(series_id: str, limit: int = 10):

    if not API_KEY:
        raise ValueError(
            "FRED_API_KEY not found. Check your .env file."
        )

    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=(5, 30)
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "FRED API request timed out."
        )

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"FRED API request failed: {e}"
        )