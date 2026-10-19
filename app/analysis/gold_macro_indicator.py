from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, timedelta
import math
from typing import Any


HISTORICAL_MACRO_WEIGHTS = {
    "cpi_acceleration": 0.20,
    "core_pce_acceleration": 0.20,
    "real_yield_change": 0.40,
    "fed_funds_change": 0.15,
    "unemployment_change": 0.05,
}

HISTORICAL_RELEASE_LAGS = {
    "cpi": 45,
    "core_pce": 45,
    "real_yield_10y": 1,
    "fed_funds_rate": 45,
    "unemployment": 45,
}

HISTORICAL_CHANGE_THRESHOLDS = {
    "cpi_acceleration": 0.05,
    "core_pce_acceleration": 0.05,
    "real_yield_change": 0.05,
    "fed_funds_change": 0.05,
    "unemployment_change": 0.1,
}

POSITIVE_MACRO = {
    "unemployment",
    "payrolls",
    "real_gdp",
}

NEGATIVE_MACRO = {
    "cpi",
    "core_cpi",
    "pce",
    "core_pce",
    "fed_funds_rate",
    "treasury_10y",
    "treasury_2y",
    "real_yield_10y",
    "ppi",
}

WEIGHTS = {
    "cpi": 0.22,
    "core_cpi": 0.18,
    "pce": 0.20,
    "core_pce": 0.15,
    "fed_funds_rate": 0.20,
    "treasury_10y": 0.12,
    "treasury_2y": 0.10,
    "real_yield_10y": 0.18,
    "unemployment": 0.18,
    "payrolls": 0.12,
    "real_gdp": 0.12,
    "ppi": 0.10,
}


def _available_index(
    as_of: date,
    observations: list[tuple[date, float]],
    release_lag_days: int,
) -> int:
    cutoff = as_of - timedelta(days=release_lag_days)
    return bisect_right([item[0] for item in observations], cutoff) - 1


def _direction(value: float, threshold: float) -> float:
    if value > threshold:
        return 1.0
    if value < -threshold:
        return -1.0
    return 0.0


def calculate_historical_macro_score(
    as_of: date,
    macro_history: dict[str, list[tuple[date, float]]],
) -> float | None:
    """Score delayed macro changes without treating rising index levels as signals."""
    factors = {}
    for name, lag_days in HISTORICAL_RELEASE_LAGS.items():
        observations = macro_history.get(name, [])
        index = _available_index(as_of, observations, lag_days)
        if index < 1:
            return None

        current = observations[index][1]
        previous = observations[index - 1][1]
        if not math.isfinite(current) or not math.isfinite(previous):
            return None

        if name in {"cpi", "core_pce"}:
            if index < 13:
                return None
            year_ago = observations[index - 12][1]
            previous_year_ago = observations[index - 13][1]
            if year_ago == 0 or previous_year_ago == 0:
                return None
            current_yoy = (current / year_ago - 1) * 100
            previous_yoy = (previous / previous_year_ago - 1) * 100
            factors[f"{name}_acceleration"] = _direction(
                current_yoy - previous_yoy,
                HISTORICAL_CHANGE_THRESHOLDS[f"{name}_acceleration"],
            )
        else:
            factor_name = {
                "real_yield_10y": "real_yield_change",
                "fed_funds_rate": "fed_funds_change",
                "unemployment": "unemployment_change",
            }[name]
            factors[factor_name] = _direction(
                current - previous,
                HISTORICAL_CHANGE_THRESHOLDS[factor_name],
            )

    score = (
        factors["cpi_acceleration"] * HISTORICAL_MACRO_WEIGHTS["cpi_acceleration"]
        + factors["core_pce_acceleration"] * HISTORICAL_MACRO_WEIGHTS["core_pce_acceleration"]
        - factors["real_yield_change"] * HISTORICAL_MACRO_WEIGHTS["real_yield_change"]
        - factors["fed_funds_change"] * HISTORICAL_MACRO_WEIGHTS["fed_funds_change"]
        + factors["unemployment_change"] * HISTORICAL_MACRO_WEIGHTS["unemployment_change"]
    )
    return score


@dataclass
class GoldMacroSignal:
    macro_score: float
    price_score: float
    composite_score: float
    signal: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "macro_score": self.macro_score,
            "price_score": self.price_score,
            "composite_score": self.composite_score,
            "signal": self.signal,
            "reasons": self.reasons,
        }


def _score_direction(indicator: str, pct_change: float | None) -> float:
    if pct_change is None:
        return 0.0

    if pct_change > 0:
        return 1.0
    if pct_change < 0:
        return -1.0
    return 0.0


def _indicator_signal(indicator: str, pct_change: float | None) -> float:
    if pct_change is None:
        return 0.0

    direction = _score_direction(indicator, pct_change)

    if indicator in POSITIVE_MACRO:
        return direction
    if indicator in NEGATIVE_MACRO:
        return -direction

    return 0.0


def calculate_price_score(price_change_pct: float | None) -> float:
    if price_change_pct is None:
        return 0.0

    if price_change_pct > 0.5:
        return 1.0
    if price_change_pct < -0.5:
        return -1.0
    return 0.0


def calculate_gold_macro_signal(snapshot: dict[str, dict[str, Any]], gold_price_change_pct: float | None = None) -> GoldMacroSignal:
    """
    Build a simple macro-driven gold trading signal from recent macro data.

    Higher macro score implies more bullish gold conditions.
    The gold price score is a small adjustment on top of the macro score.
    """

    macro_score = 0.0
    reasons: list[str] = []

    for indicator, weight in WEIGHTS.items():
        values = snapshot.get(indicator)
        if values is None:
            continue

        pct_change = values.get("percentage_change")
        signal = _indicator_signal(indicator, pct_change)
        if signal == 0:
            continue

        macro_score += signal * weight
        direction_label = "up" if signal > 0 else "down"
        reasons.append(f"{indicator}: {direction_label} bias ({pct_change:.2f}%)")

    price_score = calculate_price_score(gold_price_change_pct)

    composite_score = (0.75 * macro_score) + (0.25 * price_score)

    if composite_score > 0.25:
        signal = "Bullish"
    elif composite_score < -0.25:
        signal = "Bearish"
    else:
        signal = "Neutral"

    return GoldMacroSignal(
        macro_score=macro_score,
        price_score=price_score,
        composite_score=composite_score,
        signal=signal,
        reasons=reasons,
    )


if __name__ == "__main__":
    sample_snapshot = {
        "cpi": {"percentage_change": 0.8},
        "fed_funds_rate": {"percentage_change": 0.4},
        "real_yield_10y": {"percentage_change": 0.2},
        "unemployment": {"percentage_change": -0.5},
        "payrolls": {"percentage_change": 0.3},
    }

    signal = calculate_gold_macro_signal(sample_snapshot, gold_price_change_pct=0.7)
    print(signal.to_dict())
