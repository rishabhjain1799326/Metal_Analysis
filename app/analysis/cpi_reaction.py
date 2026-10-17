from datetime import datetime, timedelta

from app.collectors.gold import get_gold_prices

from app.analysis.gold_reaction import (
    extract_closes,
    calculate_daily_reaction,
    find_available_price
)


def analyze_cpi_events(events):

    if not events:
        return []

    # ---------------------------------
    # Find earliest and latest CPI event
    # ---------------------------------

    release_dates = [
        datetime.strptime(
            event["release_date"],
            "%Y-%m-%d"
        )
        for event in events
    ]

    earliest_release = min(release_dates)
    latest_release = max(release_dates)

    # ---------------------------------
    # Add one day before and after
    # ---------------------------------

    start_date = (
        earliest_release - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    end_date = (
        latest_release + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    print(
        f"\nFetching gold data once:"
        f"\n{start_date} → {end_date}"
    )

    # ---------------------------------
    # ONE API REQUEST
    # ---------------------------------

    gold_data = get_gold_prices(
        interval="1day",
        start_date=start_date,
        end_date=end_date,
        outputsize=5000
    )

    # ---------------------------------
    # Convert API data to dictionary
    # ---------------------------------

    prices = extract_closes(gold_data)

    results = []

    # ---------------------------------
    # Analyze every CPI event
    # ---------------------------------

    for event in events:

        release_date = datetime.strptime(
            event["release_date"],
            "%Y-%m-%d"
        )

        # ---------------------------------
        # Previous available trading day
        # ---------------------------------

        previous_price = find_available_price(
            prices,
            release_date - timedelta(days=1),
            -1
        )

        # ---------------------------------
        # CPI release day
        # ---------------------------------

        release_price = find_available_price(
            prices,
            release_date,
            1
        )

        # ---------------------------------
        # Next available trading day
        # ---------------------------------

        next_price = find_available_price(
            prices,
            release_date + timedelta(days=1),
            1
        )

        # ---------------------------------
        # Skip if data unavailable
        # ---------------------------------

        if previous_price is None:
            continue

        if release_price is None:
            continue

        if next_price is None:
            continue

        # ---------------------------------
        # Calculate gold reaction
        # ---------------------------------

        reaction = calculate_daily_reaction(
            previous_price["price"],
            release_price["price"],
            next_price["price"]
        )

        # ---------------------------------
        # Store complete event
        # ---------------------------------

        result = {
            **event,

            "gold_previous_date":
                previous_price["date"],

            "gold_previous_close":
                previous_price["price"],

            "gold_release_date":
                release_price["date"],

            "gold_release_close":
                release_price["price"],

            "gold_next_date":
                next_price["date"],

            "gold_next_close":
                next_price["price"],

            **reaction
        }

        results.append(result)

    return results