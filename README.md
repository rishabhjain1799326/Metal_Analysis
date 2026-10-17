# Precious Metals Dashboard

A Streamlit dashboard for recent U.S. macroeconomic indicators and XAU/USD
daily gold prices. Economic data is collected from FRED; gold prices are
provided by Twelve Data.

## Run locally

1. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with API keys:

   ```text
   FRED_API_KEY=your_fred_api_key
   TWELVE_DATA_API_KEY=your_twelve_data_api_key
   ```

3. Start the dashboard from the project root:

   ```bash
   streamlit run app/dashboard.py
   ```

The dashboard caches provider responses for 15 minutes. Use **Refresh data**
in the sidebar to fetch fresh values. Macro-impact descriptions are directional
heuristics, not investment advice.

Successful FRED and Twelve Data fetches are saved to
`data/precious_metals.db`. Open the **Saved data** tab in the dashboard to
inspect stored observations. The database file is local and excluded from Git.
