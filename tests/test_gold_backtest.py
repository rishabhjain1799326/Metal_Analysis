from datetime import date
import unittest

from app.analysis.gold_backtest import run_backtest
from app.analysis.gold_macro_indicator import calculate_historical_macro_score


def monthly_observations(start_year, start_month, count, accelerating=False):
    observations = []
    year = start_year
    month = start_month
    for index in range(count):
        value = 100 + index + (0.01 * index * index if accelerating else 0)
        observations.append((date(year, month, 1), value))
        month += 1
        if month == 13:
            month = 1
            year += 1
    return observations


def bullish_macro_history():
    return {
        "cpi": monthly_observations(2020, 1, 48, accelerating=True),
        "core_pce": monthly_observations(2020, 1, 48, accelerating=True),
        "fed_funds_rate": [
            (date(2023, 10, 1), 5.5),
            (date(2023, 11, 1), 5.25),
        ],
        "unemployment": [
            (date(2023, 10, 1), 3.7),
            (date(2023, 11, 1), 3.8),
        ],
        "real_yield_10y": [
            (date(2023, 11, 1), 4.1),
            (date(2023, 11, 2), 4.0),
        ],
    }


class GoldBacktestTests(unittest.TestCase):
    def test_signal_is_scored_against_following_day_return(self):
        gold_prices = [
            (date(2024, 1, 1), 100.0),
            (date(2024, 1, 2), 102.0),
            (date(2024, 1, 3), 101.0),
            (date(2024, 1, 4), 103.0),
        ]

        results, metrics = run_backtest(gold_prices, bullish_macro_history())

        self.assertEqual(results.iloc[0]["date"], "2024-01-02")
        self.assertEqual(results.iloc[0]["next_date"], "2024-01-03")
        self.assertAlmostEqual(
            results.iloc[0]["forward_return_pct"],
            (101 / 102 - 1) * 100,
        )
        self.assertEqual(results.iloc[0]["signal"], "Bullish")
        self.assertEqual(metrics["observations"], 2)

    def test_transaction_cost_is_applied_on_position_changes(self):
        gold_prices = [
            (date(2024, 1, 1), 100.0),
            (date(2024, 1, 2), 102.0),
            (date(2024, 1, 3), 104.0),
            (date(2024, 1, 4), 106.0),
        ]

        results, _ = run_backtest(
            gold_prices,
            bullish_macro_history(),
            cost_bps=10,
        )

        self.assertEqual(results.iloc[0]["position"], 1)
        self.assertAlmostEqual(
            results.iloc[0]["strategy_return_pct"],
            (104 / 102 - 1) * 10 - 0.01,
        )
        self.assertAlmostEqual(
            results.iloc[1]["strategy_return_pct"],
            (106 / 104 - 1) * 10,
        )

    def test_macro_score_uses_delayed_changes_not_absolute_index_trend(self):
        history = bullish_macro_history()
        as_of = date(2024, 1, 2)
        score_before_future_values = calculate_historical_macro_score(as_of, history)

        history["cpi"].append((date(2024, 1, 1), 1000.0))
        score_after_future_value_added = calculate_historical_macro_score(as_of, history)

        self.assertAlmostEqual(score_before_future_values, 0.55)
        self.assertEqual(score_after_future_value_added, score_before_future_values)


if __name__ == "__main__":
    unittest.main()
