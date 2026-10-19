from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.analysis.gold_impact import analyze_gold_impact
from app.analysis.macro_snapshot import calculate_snapshot
from app.collectors.economic import get_economic_data
from app.collectors.gold import get_gold_prices
from app.storage import get_observation_count, get_observations, save_observations


st.set_page_config(
    page_title="Precious Metals | Gold & Macro",
    page_icon="◈",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 85% 0%, #27301f 0, transparent 38%),
            #10120f;
        color: #f2f0e8;
    }
    [data-testid="stMetric"] {
        background: #1a1d18;
        border: 1px solid #34392f;
        padding: 1rem 1.1rem;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] {
        color: #b8b8a8;
    }
    h1, h2, h3 {
        letter-spacing: -0.03em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=900, show_spinner=False)
def load_economic_data():
    data = get_economic_data(limit=5)
    for name, response in data.items():
        if response is not None:
            save_observations(
                source="FRED",
                series=name,
                observations=response.get("observations", []),
            )
    return data


@st.cache_data(ttl=900, show_spinner=False)
def load_gold_prices():
    data = get_gold_prices(interval="1day", outputsize=90)
    save_observations(
        source="Twelve Data",
        series="xau_usd",
        observations=data.get("values", []),
        date_key="datetime",
        value_key="close",
        unit="USD/oz",
    )
    return data


INDICATOR_LABELS = {
    "cpi": "CPI",
    "core_cpi": "Core CPI",
    "pce": "PCE",
    "core_pce": "Core PCE",
    "unemployment": "Unemployment",
    "payrolls": "Nonfarm payrolls",
    "fed_funds_rate": "Federal funds rate",
    "treasury_10y": "10-year Treasury",
    "real_yield_10y": "10-year real yield",
    "treasury_2y": "2-year Treasury",
    "real_gdp": "Real GDP",
    "ppi": "Producer prices",
}

PERCENT_INDICATORS = {
    "unemployment",
    "fed_funds_rate",
    "treasury_10y",
    "real_yield_10y",
    "treasury_2y",
}

IMPACT_INDICATORS = {
    "cpi",
    "pce",
    "unemployment",
    "fed_funds_rate",
    "treasury_10y",
    "real_yield_10y",
}


def format_value(indicator, value):
    decimals = 3 if indicator == "real_gdp" else 2
    suffix = "%" if indicator in PERCENT_INDICATORS else ""
    return f"{value:,.{decimals}f}{suffix}"


def render_macro_table(snapshot):
    rows = []
    for name, values in snapshot.items():
        rows.append(
            {
                "Indicator": INDICATOR_LABELS.get(name, name.replace("_", " ").title()),
                "Latest": format_value(name, values["current"]),
                "Latest date": values["current_date"],
                "Previous": format_value(name, values["previous"]),
                "Previous date": values["previous_date"],
                "Change": format_value(name, values["change"]),
                "Change (%)": (
                    f'{values["percentage_change"]:.2f}%'
                    if values["percentage_change"] is not None
                    else "—"
                ),
            }
        )

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No complete indicator snapshots are available yet.")


def render_saved_data():
    total = get_observation_count()
    st.caption(f"{total:,} observations saved in data/precious_metals.db")
    records = get_observations()
    if not records:
        st.info(
            "The database is ready but empty. Load the dashboard with valid API "
            "keys or select Refresh data to save observations."
        )
        return

    table = pd.DataFrame(records).rename(
        columns={
            "source": "Source",
            "series": "Series",
            "observation_date": "Date",
            "value": "Value",
            "unit": "Unit",
        }
    )
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        alt="Latest economic and gold observations saved in SQLite",
    )
    st.caption("Showing the latest 500 observations.")


def render_gold_chart():
    st.subheader("Gold · XAU/USD")
    try:
        gold_data = load_gold_prices()
    except (RuntimeError, ValueError) as exc:
        st.error(f"Could not load gold prices: {exc}")
        st.caption(
            "On Streamlit Community Cloud, open the app's Settings → Secrets "
            'and add TWELVE_DATA_API_KEY = "your key".'
        )
        return

    values = gold_data.get("values", [])
    if not values:
        st.info("The gold-price provider returned no observations.")
        return

    prices = pd.DataFrame(values)
    prices["date"] = pd.to_datetime(prices["datetime"], errors="coerce")
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    prices = prices.dropna(subset=["date", "close"]).sort_values("date")

    if prices.empty:
        st.info("No valid gold-price observations were returned.")
        return

    latest_price = prices.iloc[-1]["close"]
    previous_price = prices.iloc[-2]["close"] if len(prices) > 1 else None
    daily_change = (
        latest_price - previous_price
        if previous_price is not None
        else None
    )
    st.metric(
        "Latest close · USD/oz",
        f"${latest_price:,.2f}",
        delta=f"${daily_change:+,.2f}" if daily_change is not None else None,
    )
    st.line_chart(
        prices.set_index("date")[["close"]],
        y_label="USD per troy ounce",
        color="#d8b45a",
    )
    st.caption(
        f"Daily closes · {prices.iloc[0]['date'].date()} to "
        f"{prices.iloc[-1]['date'].date()} · Source: Twelve Data"
    )


def main():
    st.title("Precious Metals")
    st.markdown(
        "Gold-market context through the lens of inflation, rates, and growth."
    )

    with st.sidebar:
        st.markdown("## Market monitor")
        st.caption("Economic indicators are sourced from FRED.")
        if st.button("Refresh data", width="stretch"):
            load_economic_data.clear()
            load_gold_prices.clear()
        st.caption("Data is cached for 15 minutes.")

    with st.spinner("Loading economic indicators…"):
        economic_data = load_economic_data()
    snapshot = calculate_snapshot(economic_data)
    missing = [
        INDICATOR_LABELS.get(name, name)
        for name, data in economic_data.items()
        if data is None
    ]

    if missing:
        st.warning(
            "Some FRED series could not be loaded: "
            + ", ".join(missing)
            + ". Check your FRED_API_KEY and network connection."
        )

    if snapshot:
        featured = [
            ("cpi", "CPI"),
            ("fed_funds_rate", "Fed funds"),
            ("real_yield_10y", "10Y real yield"),
            ("unemployment", "Unemployment"),
        ]
        cols = st.columns(len(featured))
        for col, (name, label) in zip(cols, featured):
            values = snapshot.get(name)
            if values is None:
                col.metric(label, "Unavailable")
                continue
            delta = format_value(name, values["change"])
            col.metric(
                label,
                format_value(name, values["current"]),
                delta=f"{delta} since prior observation",
                help=f"Latest observation date: {values['current_date']}",
            )

    overview_tab, macro_tab, saved_tab = st.tabs(
        ["Overview", "Macro indicators", "Saved data"]
    )
    with overview_tab:
        left, right = st.columns((1.25, 1))
        with left:
            render_gold_chart()
        with right:
            st.subheader("Macro read-through")
            impact_count = 0
            for name in IMPACT_INDICATORS:
                values = snapshot.get(name)
                if values is None:
                    continue
                impact = analyze_gold_impact(
                    name,
                    values["current"],
                    values["previous"],
                )
                impact_count += 1
                label = INDICATOR_LABELS.get(name, name)
                st.markdown(f"**{label} · {impact['impact']}**")
                st.caption(impact["reason"])
            if not impact_count:
                st.info("Macro read-through will appear when enough data is available.")
            st.caption(
                "Directional heuristics based on recent indicator changes; "
                "not investment advice."
            )

    with macro_tab:
        st.subheader("Latest economic observations")
        render_macro_table(snapshot)
        st.caption(
            f"Snapshot calculated {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}."
        )

    with saved_tab:
        st.subheader("SQLite observations")
        render_saved_data()


if __name__ == "__main__":
    main()
