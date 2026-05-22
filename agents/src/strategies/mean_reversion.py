"""Mean reversion trading strategy using Bollinger Bands."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from agents.src.data.market_data import Signal
from agents.src.strategies.indicators import calc_rsi


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
        df["rsi"] = calc_rsi(df["close"], period=self.rsi_period)

        latest = df.iloc[-1]
        price = Decimal(str(latest["close"]))

        # Price below lower band + RSI oversold = buy
        if latest["close"] < latest["lower"] and latest["rsi"] < self.rsi_oversold:
            confidence = self._confidence_from_rsi(float(latest["rsi"]), is_buy=True)
            return Signal(
                "buy", symbol,
                confidence=confidence,
                price=price,
                reasoning=f"Price below lower BB, RSI oversold at {latest['rsi']:.1f}",
                metadata={"bb_breakout": "lower", "rsi": float(latest["rsi"])},
            )

        # Price above upper band + RSI overbought = sell
        if latest["close"] > latest["upper"] and latest["rsi"] > self.rsi_overbought:
            confidence = self._confidence_from_rsi(float(latest["rsi"]), is_buy=False)
            return Signal(
                "sell", symbol,
                confidence=confidence,
                price=price,
                reasoning=f"Price above upper BB, RSI overbought at {latest['rsi']:.1f}",
                metadata={"bb_breakout": "upper", "rsi": float(latest["rsi"])},
            )

        # Price touching band but RSI not extreme = weaker signal
        if latest["close"] < latest["lower"]:
            confidence = Decimal("0.55")
            return Signal(
                "buy", symbol,
                confidence=confidence,
                price=price,
                reasoning=f"Price below lower BB at {latest['close']:.2f}, RSI {latest['rsi']:.1f}",
                metadata={"bb_breakout": "lower", "rsi": float(latest["rsi"])},
            )

        if latest["close"] > latest["upper"]:
            confidence = Decimal("0.55")
            return Signal(
                "sell", symbol,
                confidence=confidence,
                price=price,
                reasoning=f"Price above upper BB at {latest['close']:.2f}, RSI {latest['rsi']:.1f}",
                metadata={"bb_breakout": "upper", "rsi": float(latest["rsi"])},
            )

        return Signal("hold", symbol, Decimal("0"), price, "Price within bands")

    def _confidence_from_rsi(self, rsi: float, is_buy: bool) -> Decimal:
        """Scale confidence based on how extreme RSI is.

        Oversold RSI near 0 → higher buy confidence.
        Overbought RSI near 100 → higher sell confidence.
        """
        if is_buy:
            # rsi in [0, 30] → scale 0.70 to 0.90
            raw = 0.70 + (0.20 * (1 - rsi / self.rsi_oversold))
        else:
            # rsi in [70, 100] → scale 0.70 to 0.90
            raw = 0.70 + (0.20 * ((rsi - self.rsi_overbought) / (100 - self.rsi_overbought)))
        return Decimal(str(min(0.90, raw)))
