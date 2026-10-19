import requests
from app.credentials import get_credential

BASE_URL = "https://api.twelvedata.com/time_series"


def _get_api_key() -> str:
    api_key = get_credential("TWELVE_DATA_API_KEY")
    if not api_key:
        raise ValueError(
            "TWELVE_DATA_API_KEY not found. "
            "For local use, add it to the project-root .env file. "
            "For Streamlit Community Cloud, add it under App settings > Secrets."
        )
    return api_key


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

    api_key = _get_api_key()

    params = {
        "symbol": "XAU/USD",
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key
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