def get_valid_observations(data, count=2):
    """
    Extract the latest valid observations from FRED data.
    """

    observations = []

    for item in data["observations"]:

        if item["value"] == ".":
            continue

        observations.append({
            "date": item["date"],
            "value": float(item["value"])
        })

        if len(observations) == count:
            break

    return observations


def calculate_change(current, previous):
    """
    Calculate absolute change between two observations.
    """

    return current - previous


def calculate_percentage_change(current, previous):
    """
    Calculate percentage change between two observations.
    """

    if previous == 0:
        return None

    return ((current - previous) / previous) * 100