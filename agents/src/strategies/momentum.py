"""Momentum-based trading strategy."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pandas as pd


@dataclass
class Signal:
    action: str
    symbol: str
    confidence: Decimal
    price: Decimal
    reasoning: str


class MomentumStrategy:
    """Trades trend-following signals: RSI, MACD, EMA crossovers."""

    def __init__(
        self,
        rsi_period: int = 14,
        ema_fast: int = 12,
        ema_slow: int = 26,
        rsi_overbought: float = 70,
        rsi_oversold: float = 30,
    ) -> None:
        self.rsi_period = rsi_period
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        if len(df) < self.ema_slow + self.rsi_period:
            return Signal("hold", symbol, Decimal("0"), Decimal("0"), "Insufficient data")

        df = df.copy()
        df["ema_fast"] = df["close"].ewm(span=self.ema_fast).mean()
        df["ema_slow"] = df["close"].ewm(span=self.ema_slow).mean()
        df["rsi"] = self._calc_rsi(df["close"])

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price = Decimal(str(latest["close"]))

        # EMA crossover: fast crosses above slow = bullish
        if prev["ema_fast"] <= prev["ema_slow"] and latest["ema_fast"] > latest["ema_slow"]:
            return Signal(
                "buy", symbol,
                confidence=Decimal("0.75"),
                price=price,
                reasoning=f"Bullish EMA crossover. RSI: {latest['rsi']:.1f}",
            )

        # EMA crossover: fast crosses below slow = bearish
        if prev["ema_fast"] >= prev["ema_slow"] and latest["ema_fast"] < latest["ema_slow"]:
            return Signal(
                "sell", symbol,
                confidence=Decimal("0.75"),
                price=price,
                reasoning=f"Bearish EMA crossover. RSI: {latest['rsi']:.1f}",
            )

        # RSI momentum continuation
        if latest["rsi"] > self.rsi_overbought:
            return Signal(
                "sell", symbol,
                confidence=Decimal("0.60"),
                price=price,
                reasoning=f"RSI overbought at {latest['rsi']:.1f}",
            )

        if latest["rsi"] < self.rsi_oversold:
            return Signal(
                "buy", symbol,
                confidence=Decimal("0.60"),
                price=price,
                reasoning=f"RSI oversold at {latest['rsi']:.1f}",
            )

        return Signal("hold", symbol, Decimal("0"), price, "No momentum signal")

    def _calc_rsi(self, prices: pd.Series, period: int | None = None) -> pd.Series:
        period = period or self.rsi_period
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
