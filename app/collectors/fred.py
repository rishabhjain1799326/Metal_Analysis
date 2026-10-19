import requests
from app.credentials import get_credential

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_series(
    series_id: str,
    limit: int = 10,
    observation_start: str | None = None,
    observation_end: str | None = None,
    sort_order: str = "desc",
):

    api_key = get_credential("FRED_API_KEY")
    if not api_key:
        raise ValueError(
            "FRED_API_KEY not found. "
            "For local use, add it to the project-root .env file. "
            "For Streamlit Community Cloud, add it under App settings > Secrets."
        )

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": sort_order,
        "limit": limit
    }

    if observation_start:
        params["observation_start"] = observation_start

    if observation_end:
        params["observation_end"] = observation_end

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