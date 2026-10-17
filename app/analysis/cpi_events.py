from datetime import datetime


def build_cpi_events(release_dates, observations):
    """
    Combine CPI release dates with CPI observations.

    release_dates:
        FRED CPI release dates

    observations:
        CPI observations from FRED
    """

    # Remove missing CPI observations
    valid_observations = [
        item for item in observations
        if item["value"] != "."
    ]

    # Convert to a convenient structure
    observation_map = {}

    for item in valid_observations:

        observation_map[item["date"]] = float(
            item["value"]
        )

    events = []

    for release in release_dates:

        release_date = release["date"]

        # Convert release date to datetime
        release_dt = datetime.strptime(
            release_date,
            "%Y-%m-%d"
        )

        # CPI release normally reports the previous month.
        if release_dt.month == 1:
            observation_year = release_dt.year - 1
            observation_month = 12
        else:
            observation_year = release_dt.year
            observation_month = release_dt.month - 1

        observation_period = (
            f"{observation_year:04d}-"
            f"{observation_month:02d}-01"
        )

        actual = observation_map.get(
            observation_period
        )

        events.append({
            "event_type": "CPI",
            "release_date": release_date,
            "observation_period": observation_period,
            "actual": actual
        })

    return events