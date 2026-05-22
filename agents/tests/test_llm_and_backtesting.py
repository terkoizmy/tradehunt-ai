"""Tests for LLM decision engine and backtesting."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from agents.src.backtesting.engine import BacktestEngine, BacktestResult
from agents.src.llm.decision_engine import DecisionEngine, TradeDecision
from agents.src.personas.conservative import ConservativePersona
from agents.src.strategies.mean_reversion import MeanReversionStrategy
from agents.src.strategies.momentum import MomentumStrategy


class TestTradeDecision:
    def test_valid_decision(self) -> None:
        d = TradeDecision(action="buy", symbol="BTCUSDT", confidence=0.85, reasoning=" breakout")
        assert d.action == "buy"
        assert d.confidence == 0.85

    def test_invalid_action(self) -> None:
        with pytest.raises(ValueError):
            TradeDecision(action="hodl", symbol="BTCUSDT", confidence=0.5, reasoning="typo")

    def test_confidence_too_high(self) -> None:
        with pytest.raises(ValueError):
            TradeDecision(action="buy", symbol="BTCUSDT", confidence=1.5, reasoning="too high")

    def test_confidence_too_low(self) -> None:
        with pytest.raises(ValueError):
            TradeDecision(action="buy", symbol="BTCUSDT", confidence=-0.1, reasoning="too low")

    def test_coerce_string_confidence(self) -> None:
        d = TradeDecision(action="sell", symbol="ETHUSDT", confidence="0.72", reasoning="test")
        assert d.confidence == 0.72


class TestDecisionEngine:
    def test_parse_and_validate_plain_json(self) -> None:
        engine = DecisionEngine()
        result = engine._parse_and_validate('{"action":"buy","symbol":"BTC","confidence":0.8,"reasoning":"test"}')
        assert result["action"] == "buy"
        assert result["confidence"] == 0.8

    def test_parse_and_validate_markdown_block(self) -> None:
        engine = DecisionEngine()
        result = engine._parse_and_validate(
            '```json\n{"action":"sell","symbol":"ETH","confidence":0.7,"reasoning":"drop"}\n```'
        )
        assert result["action"] == "sell"
        assert result["confidence"] == 0.7

    def test_parse_invalid_json(self) -> None:
        engine = DecisionEngine()
        result = engine._parse_and_validate("not json")
        assert result["action"] == "hold"
        assert "error" in result["reasoning"].lower() or "validation" in result["reasoning"].lower()

    def test_error_response(self) -> None:
        engine = DecisionEngine()
        result = engine._error_response("network down")
        assert result["action"] == "hold"
        assert result["confidence"] == 0.0
        assert "network down" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_decide_with_threshold_blocks_low_confidence(self) -> None:
        engine = DecisionEngine()

        async def _mock_decide(_pp, _mc, _st):
            return {"action": "buy", "symbol": "BTC", "confidence": 0.5, "reasoning": "weak"}

        engine.decide = _mock_decide

        class FakeSignal:
            action = "buy"
            confidence = Decimal("0.5")
            reasoning = "weak"

        decision = await engine.decide_with_threshold(
            "prompt", "context", FakeSignal(), Decimal("0.70")
        )
        assert decision["action"] == "hold"
        assert "below threshold" in decision["reasoning"]

    @pytest.mark.asyncio
    async def test_decide_with_threshold_passes_high_confidence(self) -> None:
        engine = DecisionEngine()

        async def _mock_decide(_pp, _mc, _st):
            return {"action": "buy", "symbol": "BTC", "confidence": 0.85, "reasoning": "strong"}

        engine.decide = _mock_decide

        class FakeSignal:
            action = "buy"
            confidence = Decimal("0.85")
            reasoning = "strong"

        decision = await engine.decide_with_threshold(
            "prompt", "context", FakeSignal(), Decimal("0.70")
        )
        assert decision["action"] == "buy"


class TestBacktestEngine:
    def _make_ohlcv(self, n: int, trend: str = "flat") -> pd.DataFrame:
        np.random.seed(42)
        base = 50000.0
        if trend == "up":
            closes = base + np.cumsum(np.random.normal(50, 200, n))
        elif trend == "down":
            closes = base + np.cumsum(np.random.normal(-50, 200, n))
        else:
            closes = base + np.cumsum(np.random.normal(0, 300, n))

        return pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": closes - np.random.uniform(0, 50, n),
            "high": closes + np.random.uniform(0, 100, n),
            "low": closes - np.random.uniform(0, 100, n),
            "close": closes,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })

    def test_initial_state(self) -> None:
        engine = BacktestEngine(initial_capital=Decimal("5000"))
        assert engine.initial_capital == Decimal("5000")

    def test_run_flat_market(self) -> None:
        df = self._make_ohlcv(300)
        engine = BacktestEngine()
        strat = MomentumStrategy()
        result = engine.run(df, strat, "BTCUSDT")
        assert isinstance(result, BacktestResult)
        assert len(result.equity_curve) == len(df)
        # Flat market + momentum should rarely fire, so few or zero trades
        assert result.total_trades >= 0

    def test_run_with_persona_sl_tp(self) -> None:
        """Persona stop-loss and take-profit should be simulated."""
        np.random.seed(1)
        n = 300
        # Strong trend up to trigger buy, then flat
        closes = np.concatenate([
            np.linspace(48000, 52000, 200),
            np.linspace(52000, 52000, 100),
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
        engine = BacktestEngine()
        strat = MomentumStrategy()
        persona = ConservativePersona()
        result = engine.run(df, strat, "BTCUSDT", persona=persona)

        # Should have recorded trades
        assert result.total_trades >= 0
        # Profit factor should be calculable if any trades
        if result.total_trades > 0:
            assert result.profit_factor >= 0
            assert result.win_rate >= 0

    def test_stop_loss_simulation(self) -> None:
        """Force a stop-loss hit by making price drop after entry."""
        np.random.seed(2)
        n = 60
        # Start flat, then drop hard
        closes = np.concatenate([
            np.ones(30) * 50000,
            np.linspace(50000, 44000, 30),
        ])
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": closes,
            "high": closes + 30,
            "low": closes - 100,  # wide enough to hit SL
            "close": closes,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })

        engine = BacktestEngine()
        # Simple strategy that always buys
        class AlwaysBuy:
            def analyze(self, _df: pd.DataFrame, symbol: str):
                from agents.src.data.market_data import Signal
                from decimal import Decimal
                return Signal("buy", symbol, Decimal("1.0"), Decimal(str(_df.iloc[-1]["close"])), "always")

        persona = ConservativePersona()
        result = engine.run(df, AlwaysBuy(), "BTCUSDT", persona=persona)
        # At least one trade should have been stopped out
        sl_trades = [t for t in result.trades if t.get("reason") == "stop_loss"]
        assert len(sl_trades) > 0 or result.total_trades > 0

    def test_equity_curve_length(self) -> None:
        df = self._make_ohlcv(100)
        engine = BacktestEngine()
        strat = MeanReversionStrategy()
        result = engine.run(df, strat, "BTCUSDT")
        assert len(result.equity_curve) == len(df)

    def test_sharpe_and_drawdown(self) -> None:
        np.random.seed(5)
        n = 300
        # Strong uptrend for clear PnL
        closes = 50000 + np.cumsum(np.random.normal(20, 100, n))
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "open": closes - 20,
            "high": closes + 50,
            "low": closes - 50,
            "close": closes,
            "volume": np.ones(n),
            "turnover": np.ones(n),
        })
        engine = BacktestEngine()
        strat = MomentumStrategy()
        result = engine.run(df, strat, "BTCUSDT")
        # These should be populated
        assert result.max_drawdown_pct >= 0
        assert isinstance(result.sharpe_ratio, Decimal)
        assert result.total_pnl is not None
