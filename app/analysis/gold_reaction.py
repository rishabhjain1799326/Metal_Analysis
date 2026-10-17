from datetime import timedelta


def calculate_return(start_price, end_price):
    """
    Calculate percentage return between two prices.
    """

    if start_price == 0:
        return None

    return (
        (end_price - start_price)
        / start_price
    ) * 100


def extract_closes(gold_data):
    """
    Convert Twelve Data response into:

    {
        "2026-09-10": 3650.25,
        "2026-09-11": 3672.40
    }
    """

    prices = {}

    for item in gold_data.get("values", []):

        date = item["datetime"]
        close = float(item["close"])

        prices[date] = close

    return prices


def find_available_price(prices, date, direction):
    """
    Find the nearest available gold price.

    direction = -1 → search backwards
    direction =  1 → search forwards
    """

    current_date = date

    for _ in range(7):

        date_string = current_date.strftime(
            "%Y-%m-%d"
        )

        if date_string in prices:

            return {
                "date": date_string,
                "price": prices[date_string]
            }

        current_date += timedelta(
            days=direction
        )

    return None


def calculate_daily_reaction(
    previous_price,
    release_price,
    next_price
):
    """
    Calculate gold's reaction around the CPI release.
    """

    release_day_return = calculate_return(
        previous_price,
        release_price
    )

    next_day_return = calculate_return(
        release_price,
        next_price
    )

    return {
        "release_day_return": release_day_return,
        "next_day_return": next_day_return
    }