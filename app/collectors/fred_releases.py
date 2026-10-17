import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("FRED_API_KEY")

BASE_URL = "https://api.stlouisfed.org/fred/release/dates"


def get_release_dates(
    release_id: int,
    limit: int = 20
):
    """
    Fetch historical release dates for a FRED release.
    """

    if not API_KEY:
        raise ValueError(
            "FRED_API_KEY not found. "
            "Check your .env file."
        )

    params = {
        "release_id": release_id,
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

        data = response.json()

        if "release_dates" not in data:
            raise RuntimeError(
                "Unexpected response from FRED release API."
            )

        return data["release_dates"]

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "FRED release API request timed out."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"FRED release API request failed: {e}"
        )