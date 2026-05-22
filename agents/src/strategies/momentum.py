"""Momentum-based trading strategy."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from agents.src.data.market_data import Signal
from agents.src.strategies.indicators import calc_rsi


class MomentumStrategy:
    """Trades trend-following signals: RSI, MACD, EMA crossovers."""

    def __init__(
        self,
        rsi_period: int = 14,
        ema_fast: int = 12,
        ema_slow: int = 26,
        macd_signal: int = 9,
        rsi_overbought: float = 70,
        rsi_oversold: float = 30,
    ) -> None:
        self.rsi_period = rsi_period
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.macd_signal = macd_signal
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        if len(df) < self.ema_slow + self.rsi_period + self.macd_signal:
            return Signal("hold", symbol, Decimal("0"), Decimal("0"), "Insufficient data")

        df = df.copy()
        df["ema_fast"] = df["close"].ewm(span=self.ema_fast).mean()
        df["ema_slow"] = df["close"].ewm(span=self.ema_slow).mean()
        df["rsi"] = calc_rsi(df["close"], period=self.rsi_period)
        df["macd"], df["macd_signal"] = self._calc_macd(df["close"])

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price = Decimal(str(latest["close"]))

        # Combined EMA + MACD signal for stronger conviction
        ema_bull = prev["ema_fast"] <= prev["ema_slow"] and latest["ema_fast"] > latest["ema_slow"]
        ema_bear = prev["ema_fast"] >= prev["ema_slow"] and latest["ema_fast"] < latest["ema_slow"]
        macd_bull = prev["macd"] <= prev["macd_signal"] and latest["macd"] > latest["macd_signal"]
        macd_bear = prev["macd"] >= prev["macd_signal"] and latest["macd"] < latest["macd_signal"]

        if ema_bull and macd_bull:
            return Signal(
                "buy", symbol,
                confidence=Decimal("0.90"),
                price=price,
                reasoning=f"Strong bullish EMA+MACD crossover. RSI: {latest['rsi']:.1f}",
                metadata={"ema_cross": True, "macd_cross": True, "rsi": float(latest["rsi"])},
            )

        if ema_bear and macd_bear:
            return Signal(
                "sell", symbol,
                confidence=Decimal("0.90"),
                price=price,
                reasoning=f"Strong bearish EMA+MACD crossover. RSI: {latest['rsi']:.1f}",
                metadata={"ema_cross": True, "macd_cross": True, "rsi": float(latest["rsi"])},
            )

        # EMA crossover alone
        if ema_bull:
            return Signal(
                "buy", symbol,
                confidence=Decimal("0.75"),
                price=price,
                reasoning=f"Bullish EMA crossover. RSI: {latest['rsi']:.1f}",
                metadata={"ema_cross": True, "rsi": float(latest["rsi"])},
            )

        if ema_bear:
            return Signal(
                "sell", symbol,
                confidence=Decimal("0.75"),
                price=price,
                reasoning=f"Bearish EMA crossover. RSI: {latest['rsi']:.1f}",
                metadata={"ema_cross": True, "rsi": float(latest["rsi"])},
            )

        # MACD crossover alone
        if macd_bull:
            return Signal(
                "buy", symbol,
                confidence=Decimal("0.70"),
                price=price,
                reasoning=f"Bullish MACD crossover. RSI: {latest['rsi']:.1f}",
                metadata={"macd_cross": True, "rsi": float(latest["rsi"])},
            )

        if macd_bear:
            return Signal(
                "sell", symbol,
                confidence=Decimal("0.70"),
                price=price,
                reasoning=f"Bearish MACD crossover. RSI: {latest['rsi']:.1f}",
                metadata={"macd_cross": True, "rsi": float(latest["rsi"])},
            )

        # RSI momentum continuation (no crossover)
        if latest["rsi"] > self.rsi_overbought:
            return Signal(
                "sell", symbol,
                confidence=Decimal("0.55"),
                price=price,
                reasoning=f"RSI overbought at {latest['rsi']:.1f}",
                metadata={"rsi": float(latest["rsi"])},
            )

        if latest["rsi"] < self.rsi_oversold:
            return Signal(
                "buy", symbol,
                confidence=Decimal("0.55"),
                price=price,
                reasoning=f"RSI oversold at {latest['rsi']:.1f}",
                metadata={"rsi": float(latest["rsi"])},
            )

        return Signal("hold", symbol, Decimal("0"), price, "No momentum signal")

    def _calc_macd(self, prices: pd.Series) -> tuple[pd.Series, pd.Series]:
        ema_fast = prices.ewm(span=self.ema_fast).mean()
        ema_slow = prices.ewm(span=self.ema_slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=self.macd_signal).mean()
        return macd, signal
