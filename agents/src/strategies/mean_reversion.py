"""Mean reversion trading strategy using Bollinger Bands."""

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


class MeanReversionStrategy:
    """Trades price extremes with Bollinger Bands and RSI."""

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
    ) -> None:
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        if len(df) < self.bb_period + self.rsi_period:
            return Signal("hold", symbol, Decimal("0"), Decimal("0"), "Insufficient data")

        df = df.copy()
        df["sma"] = df["close"].rolling(self.bb_period).mean()
        df["std"] = df["close"].rolling(self.bb_period).std()
        df["upper"] = df["sma"] + self.bb_std * df["std"]
        df["lower"] = df["sma"] - self.bb_std * df["std"]
        df["rsi"] = self._calc_rsi(df["close"])

        latest = df.iloc[-1]
        price = Decimal(str(latest["close"]))

        # Price below lower band + RSI oversold = buy
        if latest["close"] < latest["lower"] and latest["rsi"] < self.rsi_oversold:
            confidence = min(Decimal("0.90"), Decimal(str(1 - latest["rsi"] / 100)))
            return Signal(
                "buy", symbol,
                confidence=confidence,
                price=price,
                reasoning=f"Price below lower BB, RSI oversold at {latest['rsi']:.1f}",
            )

        # Price above upper band + RSI overbought = sell
        if latest["close"] > latest["upper"] and latest["rsi"] > self.rsi_overbought:
            confidence = min(Decimal("0.90"), Decimal(str(latest["rsi"] / 100)))
            return Signal(
                "sell", symbol,
                confidence=confidence,
                price=price,
                reasoning=f"Price above upper BB, RSI overbought at {latest['rsi']:.1f}",
            )

        return Signal("hold", symbol, Decimal("0"), price, "Price within bands")

    def _calc_rsi(self, prices: pd.Series, period: int | None = None) -> pd.Series:
        period = period or self.rsi_period
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
