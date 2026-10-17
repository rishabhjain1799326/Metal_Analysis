from app.collectors.economic import get_economic_data
from app.analysis.macro_snapshot import calculate_snapshot


def main():

    # =========================================================
    # 1. COLLECT ECONOMIC DATA FROM FRED
    # =========================================================

    print("\n")
    print("=" * 60)
    print("        ECONOMIC DATA")
    print("=" * 60)

    economic_data = get_economic_data(
        limit=5
    )

    # Display raw economic data
    for name, data in economic_data.items():

        print(f"\n{name}")

        if data is None:
            print("  No data available")
            continue

        observations = data.get(
            "observations",
            []
        )

        for observation in observations[:2]:

            print(
                f"  {observation['date']} "
                f"→ {observation['value']}"
            )


    # =========================================================
    # 2. CALCULATE MACRO SNAPSHOT
    # =========================================================

    snapshot = calculate_snapshot(
        economic_data
    )


    # =========================================================
    # 3. DISPLAY MACRO SNAPSHOT
    # =========================================================

    print("\n")
    print("=" * 60)
    print("        MACRO SNAPSHOT")
    print("=" * 60)

    for name, data in snapshot.items():

        print(f"\n{name}")

        print(
            f"  Current  : "
            f"{data['current']}"
        )

        print(
            f"  Previous : "
            f"{data['previous']}"
        )

        print(
            f"  Change   : "
            f"{data['change']:.3f}"
        )

        if data["percentage_change"] is not None:

            print(
                f"  % Change : "
                f"{data['percentage_change']:.3f}%"
            )


# =============================================================
# PROGRAM ENTRY POINT
# =============================================================

if __name__ == "__main__":
    main()