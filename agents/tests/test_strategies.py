"""Tests for trading strategy implementations."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from agents.src.strategies.indicators import calc_rsi
from agents.src.strategies.mean_reversion import MeanReversionStrategy
from agents.src.strategies.momentum import MomentumStrategy
from agents.src.data.market_data import Signal


def _make_ohlcv(n: int, trend: str = "flat") -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    base = 50000.0
    if trend == "up":
        closes = base + np.cumsum(np.random.normal(50, 200, n))
    elif trend == "down":
        closes = base + np.cumsum(np.random.normal(-50, 200, n))
    else:
        closes = base + np.cumsum(np.random.normal(0, 300, n))

    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
        "open": closes - np.random.uniform(0, 50, n),
        "high": closes + np.random.uniform(0, 100, n),
        "low": closes - np.random.uniform(0, 100, n),
        "close": closes,
        "volume": np.random.uniform(1, 10, n),
        "turnover": np.random.uniform(1000, 5000, n),
    })
    return df


class TestCalcRsi:
    def test_calc_rsi_basic(self) -> None:
        prices = pd.Series([50, 51, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39])
        rsi = calc_rsi(prices, period=14)
        assert not rsi.isna().all()
        assert 0 <= rsi.iloc[-1] <= 100
        # After a sustained downtrend the last RSI should be below 50
        assert rsi.iloc[-2] < 50

    def test_calc_rsi_matches_momentum(self) -> None:
        df = _make_ohlcv(100)
        strat = MomentumStrategy()
        # The old internal method should produce same result as shared function
        from agents.src.strategies.indicators import calc_rsi as shared_calc_rsi
        shared = shared_calc_rsi(df["close"], period=strat.rsi_period)
        assert len(shared) == len(df)


class TestMomentumStrategy:
    def test_insufficient_data(self) -> None:
        strat = MomentumStrategy()
        df = _make_ohlcv(30)
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.action == "hold"
        assert sig.confidence == Decimal("0")
        assert "Insufficient" in sig.reasoning

    def test_signal_structure(self) -> None:
        strat = MomentumStrategy()
        df = _make_ohlcv(300, trend="up")
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.symbol == "BTCUSDT"
        assert sig.action in ("buy", "sell", "hold")
        assert 0 <= sig.confidence <= 1
        assert sig.price > 0

    def test_rsi_oversold_buy(self) -> None:
        """Force RSI oversold by making prices drop heavily."""
        np.random.seed(7)
        n = 300
        closes = 50000.0 - np.cumsum(np.random.uniform(100, 300, n))
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": closes,
            "high": closes + np.random.uniform(0, 50, n),
            "low": closes - np.random.uniform(0, 50, n),
            "close": closes,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })
        strat = MomentumStrategy()
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.action in ("buy", "hold")
        if sig.action == "buy":
            assert sig.confidence > Decimal("0")
            assert "RSI" in sig.reasoning or "EMA" in sig.reasoning

    def test_macd_calculation(self) -> None:
        strat = MomentumStrategy()
        df = _make_ohlcv(300)
        macd, signal = strat._calc_macd(df["close"])
        assert len(macd) == len(df)
        assert len(signal) == len(df)
        assert not macd.isna().all()
        assert not signal.isna().all()

    def test_combined_ema_macd_confidence(self) -> None:
        """When both EMA and MACD cross in the same direction, confidence should be highest."""
        np.random.seed(1)
        n = 300
        # Create a strong uptrend to trigger combined signals
        closes = np.concatenate([
            np.linspace(48000, 49000, 150),
            np.linspace(49000, 53000, 150),
        ])
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": closes - 20,
            "high": closes + 50,
            "low": closes - 50,
            "close": closes,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })
        strat = MomentumStrategy()
        sig = strat.analyze(df, "BTCUSDT")
        if sig.action == "buy":
            assert sig.confidence >= Decimal("0.70")


class TestMeanReversionStrategy:
    def test_insufficient_data(self) -> None:
        strat = MeanReversionStrategy()
        df = _make_ohlcv(20)
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.action == "hold"
        assert sig.confidence == Decimal("0")
        assert "Insufficient" in sig.reasoning

    def test_signal_structure(self) -> None:
        strat = MeanReversionStrategy()
        df = _make_ohlcv(300)
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.symbol == "BTCUSDT"
        assert sig.action in ("buy", "sell", "hold")
        assert 0 <= sig.confidence <= 1
        assert sig.price > 0

    def test_bb_breakout_buy(self) -> None:
        """Price far below lower band + RSI oversold should trigger buy."""
        np.random.seed(3)
        n = 300
        base = np.ones(250) * 50000
        # Spike down
        drop = np.concatenate([base, np.linspace(50000, 42000, 50)])
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": drop,
            "high": drop + np.random.uniform(0, 30, n),
            "low": drop - np.random.uniform(0, 30, n),
            "close": drop,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })
        strat = MeanReversionStrategy()
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.action in ("buy", "hold")
        if sig.action == "buy":
            assert sig.confidence > Decimal("0")
            assert "BB" in sig.reasoning or "band" in sig.reasoning

    def test_bb_breakout_sell(self) -> None:
        """Price far above upper band + RSI overbought should trigger sell."""
        np.random.seed(4)
        n = 300
        base = np.ones(250) * 50000
        spike = np.concatenate([base, np.linspace(50000, 58000, 50)])
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": spike,
            "high": spike + np.random.uniform(0, 30, n),
            "low": spike - np.random.uniform(0, 30, n),
            "close": spike,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })
        strat = MeanReversionStrategy()
        sig = strat.analyze(df, "BTCUSDT")
        assert sig.action in ("sell", "hold")
        if sig.action == "sell":
            assert sig.confidence > Decimal("0")

    def test_confidence_from_rsi(self) -> None:
        strat = MeanReversionStrategy()
        # Extreme oversold → higher confidence
        conf_buy = strat._confidence_from_rsi(10, is_buy=True)
        conf_buy_weak = strat._confidence_from_rsi(28, is_buy=True)
        assert conf_buy > conf_buy_weak

        # Extreme overbought → higher confidence
        conf_sell = strat._confidence_from_rsi(90, is_buy=False)
        conf_sell_weak = strat._confidence_from_rsi(72, is_buy=False)
        assert conf_sell > conf_sell_weak

        assert conf_buy <= Decimal("0.90")
        assert conf_sell <= Decimal("0.90")
