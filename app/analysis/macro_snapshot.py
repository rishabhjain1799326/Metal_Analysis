def get_valid_values(data, count=2):

    values = []

    for item in data.get("observations", []):

        if item["value"] == ".":
            continue

        values.append({
            "date": item["date"],
            "value": float(item["value"])
        })

        if len(values) == count:
            break

    return values


def calculate_snapshot(data):

    snapshot = {}

    for name, series in data.items():

        if not series:
            continue

        values = get_valid_values(
            series,
            2
        )

        if len(values) < 2:
            continue

        current = values[0]
        previous = values[1]

        change = (
            current["value"]
            - previous["value"]
        )

        if previous["value"] != 0:

            percentage_change = (
                change
                / previous["value"]
            ) * 100

        else:

            percentage_change = None

        snapshot[name] = {

            "current_date":
                current["date"],

            "current":
                current["value"],

            "previous_date":
                previous["date"],

            "previous":
                previous["value"],

            "change":
                change,

            "percentage_change":
                percentage_change
        }

    return snapshot