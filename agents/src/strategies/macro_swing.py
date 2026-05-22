"""Multi-timeframe macro swing strategy."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from agents.src.data.market_data import Signal


class MacroSwingStrategy:
    """Analyzes multiple timeframes for trend alignment."""

    def __init__(self) -> None:
        self.timeframes = {
            "short": {"period": 20, "weight": Decimal("0.3")},
            "medium": {"period": 50, "weight": Decimal("0.3")},
            "long": {"period": 200, "weight": Decimal("0.4")},
        }

    def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        if len(df) < 200:
            return Signal("hold", symbol, Decimal("0"), Decimal("0"), "Insufficient data")

        price = Decimal(str(df.iloc[-1]["close"]))
        score = Decimal("0")

        for tf_name, tf in self.timeframes.items():
            if len(df) >= tf["period"]:
                sma = df["close"].rolling(tf["period"]).mean().iloc[-1]
                if price > Decimal(str(sma)):
                    score += tf["weight"]
                else:
                    score -= tf["weight"]

        if score > Decimal("0.3"):
            return Signal(
                "buy", symbol,
                confidence=abs(score),
                price=price,
                reasoning=f"Multi-timeframe bullish alignment, score: {score:.2f}",
                metadata={"swing_score": float(score)},
            )
        elif score < Decimal("-0.3"):
            return Signal(
                "sell", symbol,
                confidence=abs(score),
                price=price,
                reasoning=f"Multi-timeframe bearish alignment, score: {score:.2f}",
                metadata={"swing_score": float(score)},
            )

        return Signal(
            "hold", symbol, Decimal("0"), price,
            f"No alignment, score: {score:.2f}",
        )
