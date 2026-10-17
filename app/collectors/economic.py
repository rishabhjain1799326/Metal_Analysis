from app.collectors.fred import get_series
from app.config import FRED_SERIES


def get_economic_data(limit=10):
    """
    Collect the latest observations for all configured
    economic indicators.
    """

    data = {}

    for name, series_id in FRED_SERIES.items():

        try:
            response = get_series(
                series_id,
                limit=limit
            )

            data[name] = response

        except Exception as e:

            print(
                f"Failed to fetch {name}: {e}"
            )

            data[name] = None

    return data