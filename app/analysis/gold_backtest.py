from __future__ import annotations

import argparse
from datetime import date, timedelta
import math
from pathlib import Path
import statistics
from typing import Any

import pandas as pd

from app.analysis.gold_macro_indicator import calculate_historical_macro_score
from app.collectors.fred import get_series
from app.collectors.gold import get_gold_prices
from app.config import FRED_SERIES
from app.storage import save_observations


FRED_LIMIT = 100_000
GOLD_OUTPUT_SIZE = 5_000
TRADING_DAYS_PER_YEAR = math.sqrt(252)

def _clean_observations(
    observations: list[dict[str, Any]],
) -> list[tuple[date, float]]:
    clean = []
    for observation in observations:
        raw_value = observation.get("value")
        if raw_value in (None, "."):
            continue
        value = float(raw_value)
        if not math.isfinite(value):
            continue
        clean.append((date.fromisoformat(str(observation["date"])[:10]), value))
    return sorted(clean)


def _total_return(returns: list[float]) -> float:
    return (math.prod(1 + value / 100 for value in returns) - 1) * 100


def run_backtest(
    gold_prices: list[tuple[date, float]],
    macro_history: dict[str, list[tuple[date, float]]],
    cost_bps: float = 0,
    momentum_bars: int = 5,
    momentum_threshold: float = 1.0,
    position_size_pct: float = 10,
    trade_mode: str = "long_only",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Evaluate close-based signals against the following trading day's return."""
    if cost_bps < 0:
        raise ValueError("cost_bps cannot be negative.")
    if momentum_bars < 1:
        raise ValueError("momentum_bars must be at least 1.")
    if momentum_threshold < 0:
        raise ValueError("momentum_threshold cannot be negative.")
    if not 0 < position_size_pct <= 100:
        raise ValueError("position_size_pct must be greater than 0 and at most 100.")
    if trade_mode not in {"long_only", "long_short"}:
        raise ValueError("trade_mode must be 'long_only' or 'long_short'.")

    prices_by_date = {price_date: close for price_date, close in gold_prices}
    prices = sorted(prices_by_date.items())
    if len(prices) < 3:
        raise ValueError("At least three gold closing prices are required.")
    if any(close <= 0 or not math.isfinite(close) for _, close in prices):
        raise ValueError("Gold closing prices must be positive finite numbers.")

    normalized_macro = {
        name: sorted({observation_date: value for observation_date, value in values}.items())
        for name, values in macro_history.items()
    }

    records = []
    previous_position = 0
    for index in range(1, len(prices) - 1):
        current_date, current_close = prices[index]
        next_date, next_close = prices[index + 1]
        macro_score = calculate_historical_macro_score(current_date, normalized_macro)
        if index >= momentum_bars:
            momentum_base = prices[index - momentum_bars][1]
            price_change_pct = (current_close / momentum_base - 1) * 100
            price_score = (
                1.0 if price_change_pct > momentum_threshold
                else -1.0 if price_change_pct < -momentum_threshold
                else 0.0
            )
        else:
            price_change_pct = None
            price_score = 0.0

        composite_score = (
            0.75 * macro_score + 0.25 * price_score
            if macro_score is not None
            else None
        )
        signal = (
            "Bullish"
            if composite_score is not None and composite_score > 0.25
            else "Bearish"
            if composite_score is not None and composite_score < -0.25
            else "Neutral"
            if composite_score is not None
            else "Unavailable"
        )
        position = (
            1
            if signal == "Bullish"
            else -1
            if signal == "Bearish" and trade_mode == "long_short"
            else 0
        )

        forward_return_pct = ((next_close - current_close) / current_close) * 100
        turnover = abs(position - previous_position)
        strategy_return_pct = (
            position * forward_return_pct * position_size_pct / 100
            - turnover * position_size_pct * cost_bps / 10_000
        )
        buy_hold_return_pct = forward_return_pct * position_size_pct / 100

        records.append({
            "date": current_date.isoformat(),
            "next_date": next_date.isoformat(),
            "close": current_close,
            "signal": signal,
            "macro_score": macro_score,
            "price_change_pct": price_change_pct,
            "price_score": price_score,
            "composite_score": composite_score,
            "position": position,
            "forward_return_pct": forward_return_pct,
            "strategy_return_pct": strategy_return_pct,
            "buy_hold_return_pct": buy_hold_return_pct,
            "turnover": turnover,
        })
        previous_position = position

    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError("No forward-return rows could be calculated.")

    strategy_returns = frame["strategy_return_pct"].tolist()
    benchmark_returns = frame["buy_hold_return_pct"].tolist()
    active_returns = frame.loc[frame["position"] != 0, "strategy_return_pct"]
    standard_deviation = (
        statistics.stdev(strategy_returns) if len(strategy_returns) > 1 else 0
    )
    sharpe = (
        statistics.mean(strategy_returns) / standard_deviation * TRADING_DAYS_PER_YEAR
        if standard_deviation
        else None
    )
    strategy_curve = [
        math.prod(1 + value / 100 for value in strategy_returns[:index + 1])
        for index in range(len(strategy_returns))
    ]
    running_peak = 1.0
    max_drawdown_pct = 0.0
    for value in strategy_curve:
        running_peak = max(running_peak, value)
        max_drawdown_pct = min(max_drawdown_pct, (value / running_peak - 1) * 100)

    trades = sum(
        position != 0 and position != previous
        for previous, position in zip(
            [0, *frame["position"].tolist()[:-1]],
            frame["position"].tolist(),
        )
    )
    metrics = {
        "observations": len(frame),
        "strategy_total_return_pct": _total_return(strategy_returns),
        "buy_hold_total_return_pct": _total_return(benchmark_returns),
        "gold_asset_buy_hold_return_pct": _total_return(
            frame["forward_return_pct"].tolist()
        ),
        "annualized_sharpe": sharpe,
        "max_drawdown_pct": max_drawdown_pct,
        "active_hit_rate_pct": (
            (active_returns.gt(0).mean() * 100) if not active_returns.empty else None
        ),
        "trades": int(trades),
        "trade_mode": trade_mode,
        "position_size_pct": position_size_pct,
        "data_unavailable_days": int(frame["signal"].eq("Unavailable").sum()),
        "bullish_days": int(frame["signal"].eq("Bullish").sum()),
        "bearish_days": int(frame["signal"].eq("Bearish").sum()),
        "neutral_days": int(frame["signal"].eq("Neutral").sum()),
    }
    return frame, metrics


def _fetch_history(start: date, end: date) -> tuple[list[tuple[date, float]], dict[str, list[tuple[date, float]]]]:
    macro_history = {}
    macro_start = start - timedelta(days=450)
    for name, series_id in FRED_SERIES.items():
        response = get_series(
            series_id,
            limit=FRED_LIMIT,
            observation_start=macro_start.isoformat(),
            observation_end=end.isoformat(),
            sort_order="asc",
        )
        observations = response.get("observations", [])
        if not observations:
            raise RuntimeError(f"FRED returned no observations for {name} ({series_id}).")
        save_observations(source="FRED", series=name, observations=observations)
        macro_history[name] = _clean_observations(observations)
        if not macro_history[name]:
            raise RuntimeError(f"FRED returned no usable values for {name} ({series_id}).")

    gold_response = get_gold_prices(
        interval="1day",
        outputsize=GOLD_OUTPUT_SIZE,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
    gold_observations = gold_response.get("values", [])
    if not gold_observations:
        raise RuntimeError("Twelve Data returned no XAU/USD daily prices.")
    save_observations(
        source="Twelve Data",
        series="xau_usd",
        observations=gold_observations,
        date_key="datetime",
        value_key="close",
        unit="USD/oz",
    )
    gold_prices = _clean_observations([
        {"date": value.get("datetime"), "value": value.get("close")}
        for value in gold_observations
    ])
    return gold_prices, macro_history


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtest the gold macro signal using FRED and Twelve Data history."
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=365 * 5),
        help="First date to fetch (YYYY-MM-DD; defaults to roughly five years ago).",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=date.today(),
        help="Last date to fetch (YYYY-MM-DD; defaults to today).",
    )
    parser.add_argument(
        "--cost-bps",
        type=float,
        default=0,
        help="Transaction cost in basis points per unit of position turnover.",
    )
    parser.add_argument(
        "--momentum-bars",
        type=int,
        default=5,
        help="Gold-price momentum lookback in daily bars (default: 5).",
    )
    parser.add_argument(
        "--momentum-threshold",
        type=float,
        default=1.0,
        help="Gold-price momentum threshold in percent (default: 1.0).",
    )
    parser.add_argument(
        "--position-size-pct",
        type=float,
        default=10,
        help="Percent of equity allocated to each position (default: 10).",
    )
    parser.add_argument(
        "--trade-mode",
        choices=("long_only", "long_short"),
        default="long_only",
        help="Use long-only or long/short positions (default: long_only).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/gold_macro_backtest.csv"),
        help="Where to write the daily backtest results.",
    )
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start.")
    if args.cost_bps < 0:
        parser.error("--cost-bps cannot be negative.")
    if args.momentum_bars < 1:
        parser.error("--momentum-bars must be at least 1.")
    if args.momentum_threshold < 0:
        parser.error("--momentum-threshold cannot be negative.")
    if not 0 < args.position_size_pct <= 100:
        parser.error("--position-size-pct must be greater than 0 and at most 100.")

    gold_prices, macro_history = _fetch_history(args.start, args.end)
    results, metrics = run_backtest(
        gold_prices,
        macro_history,
        args.cost_bps,
        args.momentum_bars,
        args.momentum_threshold,
        args.position_size_pct,
        args.trade_mode,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)

    print(f"Backtest dates: {results.iloc[0]['date']} to {results.iloc[-1]['next_date']}")
    print(f"Daily observations tested: {metrics['observations']}")
    print(f"Strategy return: {metrics['strategy_total_return_pct']:.2f}%")
    print(f"Buy-and-hold return: {metrics['buy_hold_total_return_pct']:.2f}%")
    print(
        "Gold buy-and-hold asset return (100% exposure): "
        f"{metrics['gold_asset_buy_hold_return_pct']:.2f}%"
    )
    print(
        "Annualized Sharpe: "
        + (
            f"{metrics['annualized_sharpe']:.2f}"
            if metrics["annualized_sharpe"] is not None
            else "not available"
        )
    )
    print(f"Maximum drawdown: {metrics['max_drawdown_pct']:.2f}%")
    print(
        "Active hit rate: "
        + (
            f"{metrics['active_hit_rate_pct']:.2f}%"
            if metrics["active_hit_rate_pct"] is not None
            else "not available"
        )
    )
    print(
        f"Trades: {metrics['trades']} "
        f"(bullish days {metrics['bullish_days']}, "
        f"bearish days {metrics['bearish_days']}, "
        f"neutral days {metrics['neutral_days']}, "
        f"unavailable days {metrics['data_unavailable_days']})"
    )
    print(
        f"Trade mode: {metrics['trade_mode']}; "
        f"position size: {metrics['position_size_pct']:.1f}% of equity"
    )
    print(f"Daily results saved to {args.output}")
    print(
        "Caution: FRED observation dates are delayed approximately, but this "
        "uses revised historical values rather than real-time data vintages. "
        "Treat results as exploratory, not as evidence of a profitable strategy."
    )


if __name__ == "__main__":
    main()
