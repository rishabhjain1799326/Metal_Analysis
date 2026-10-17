import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

BASE_URL = "https://api.twelvedata.com/time_series"


def get_gold_prices(
    interval="1day",
    outputsize=30,
    start_date=None,
    end_date=None
):
    """
    Fetch historical XAU/USD gold prices
    from Twelve Data.
    """

    if not API_KEY:
        raise ValueError(
            "TWELVE_DATA_API_KEY not found. "
            "Check your .env file."
        )

    params = {
        "symbol": "XAU/USD",
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY
    }

    if start_date:
        params["start_date"] = start_date

    if end_date:
        params["end_date"] = end_date

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=(5, 30)
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") == "error":
            raise RuntimeError(
                data.get(
                    "message",
                    "Twelve Data API returned an error."
                )
            )

        return data

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "Twelve Data API request timed out."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Twelve Data API request failed: {e}"
        )