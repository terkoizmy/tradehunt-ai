"""Shared technical indicators for trading strategies."""

from __future__ import annotations

import pandas as pd


def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute the Relative Strength Index (RSI) for a price series.

    Uses Wilder's smoothing (exponential moving average).
    """
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
