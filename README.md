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

## Deploy to Streamlit Community Cloud

1. Push the project to GitHub and create a Streamlit Community Cloud app for
   this repository. Set the **Main file path** to `app/dashboard.py`.
2. In the deployed app's **Settings > Secrets**, add both API keys:

   ```toml
   FRED_API_KEY = "your_fred_api_key"
   TWELVE_DATA_API_KEY = "your_twelve_data_api_key"
   ```

   Do not commit API keys or a `.streamlit/secrets.toml` file. The local `.env`
   file is ignored by Git and is not available to the deployed app.
3. Save the secrets and reboot the app from its settings. Check the app's
   **Manage app** logs if it still fails to start.

The dashboard caches provider responses for 15 minutes. Use **Refresh data**
in the sidebar to fetch fresh values. Macro-impact descriptions are directional
heuristics, not investment advice.

Successful FRED and Twelve Data fetches are saved to
`data/precious_metals.db`. Open the **Saved data** tab in the dashboard to
inspect stored observations. The database file is local and excluded from Git.

## Backtest the gold macro signal

With both API keys configured as above, run the historical daily backtest from
the repository root:

```bash
python -m app.analysis.gold_backtest
```

It fetches roughly five years of FRED and XAU/USD history by default and writes
daily signals and forward returns to `data/gold_macro_backtest.csv`. It fetches
an additional 450 days of macro history before the test start to calculate
year-over-year inflation acceleration. Set `--start`, `--end`,
`--momentum-bars`, `--momentum-threshold`, and `--cost-bps` to adjust the test:

```bash
python -m app.analysis.gold_backtest \
  --start 2020-01-01 \
  --end 2025-12-31 \
  --momentum-bars 5 \
  --momentum-threshold 1.0 \
  --cost-bps 5 \
  --position-size-pct 10 \
  --trade-mode long_only
```

The refined macro score uses changes in year-over-year CPI and core PCE
inflation, real yields, the federal funds rate, and unemployment. Small changes
are ignored using configurable thresholds embedded in the model. Gold momentum
uses a five-bar return by default. Each signal is evaluated against the
following trading day's close-to-close return. Returns are calculated at the
configured position size (10% of equity by default) and compared with a
buy-and-hold position at the same size. The separately reported gold asset
return assumes 100% exposure. The default mode is long-only; `--trade-mode
long_short` also shorts on bearish conditions. Macro observations are delayed
approximately by 45 calendar days for monthly releases and one day for the
daily real yield. The delay is only an approximation; FRED's historical
observations can be revised, and this backtest does not use real-time data
vintages or model slippage. Results are exploratory and do not establish future
profitability.

## Test the indicator in TradingView

For one TradingView script combining macro signals and EMA crossovers, use
`app/tradingview/gold_combined_strategy.pine`. Add it to a daily XAU/USD chart
and open **Strategy Tester**. Its **Signal mode** setting lets you test
**Macro only**, **EMA crossover**, **Macro + EMA confirmation**, or **Any
signal**. The status panel shows macro and EMA states independently; BUY/SELL
labels and Strategy Tester orders follow the selected mode. Long-only is the
default. The strategy uses 10% of equity per position, 0.05% commission, and
one tick of slippage; adjust these assumptions to match your test.

The macro modes require TradingView access to the FRED symbols selected in the
settings. If the symbol data is unavailable, macro signals cannot be computed.
The historical release delays are approximate; this combines exploratory
signals and is not evidence of a profitable strategy. Compare modes on the
same chart, timeframe, costs, and dates, and keep a later period untouched for
out-of-sample evaluation.

The original individual scripts remain available below for isolated testing:

Open `app/tradingview/gold_macro_pulse.pine`, copy it into TradingView's Pine
Editor, then select **Add to chart**. Apply it to an XAU/USD chart and choose a
timeframe. It marks fast/slow EMA crossovers with **BUY**/**SELL** labels and
shades bullish/bearish trend periods. RSI confirmation is optional and off by
default. EMA lengths and RSI settings can be changed in the indicator settings.
Create alerts from the bullish or bearish crossover conditions if needed.

This Pine script is a price-only historical signal; it does not use past
macroeconomic releases or place trades. The EMA/RSI rules are a research
prototype, not validated trading advice.

To see simulated historical trades and performance statistics in TradingView's
Strategy Tester, use `app/tradingview/gold_ema_strategy.pine` instead. It
supports long-only or long-and-short tests, a date range, and optional RSI
confirmation. Its default assumptions are 10% of equity per position, 0.05%
commission per order, and one tick of slippage; adjust the strategy Properties
to better match your broker, symbol, and execution. Results are sensitive to
symbol, timeframe, available history, and costs. Compare with buy-and-hold and
test a later, untouched date range before drawing conclusions.

For the refined TradingView macro strategy based on the project's FRED data,
use `app/tradingview/gold_macro_strategy.pine`. It uses CPI and core PCE
year-over-year inflation acceleration, changes in the 10Y real yield and Fed
funds rate, and unemployment changes. It delays monthly series by two
observations and the daily real yield by one observation. Use a daily XAU/USD
chart and verify that TradingView provides the configured FRED symbols on your
account. A symbol error or the status "FRED data unavailable" means the
strategy cannot calculate signals for that data feed.

These delays do not recreate the exact release timestamps or FRED data vintages
available to traders at the time. The revised model is a hypothesis to test,
not a promise of improved performance; compare its Strategy Tester results
against buy-and-hold and an untouched date range.
