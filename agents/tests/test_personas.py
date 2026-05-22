"""Tests for quant persona implementations."""

from decimal import Decimal

import pytest

from agents.src.personas.aggressive import AggressivePersona
from agents.src.personas.arbitrageur import ArbitrageurPersona
from agents.src.personas.base import BasePersona, PersonaConfig
from agents.src.personas.conservative import ConservativePersona
from agents.src.personas.sentiment import SentimentPersona


class TestPersonaConfig:
    def test_persona_config_fields(self) -> None:
        config = PersonaConfig(
            name="Test",
            risk_profile="aggressive",
            description="A test persona.",
            max_drawdown=Decimal("0.20"),
            preferred_timeframes=["15", "60"],
            max_leverage=Decimal("3"),
            position_size_pct=Decimal("0.10"),
            stop_loss_pct=Decimal("0.02"),
            take_profit_pct=Decimal("0.06"),
            confidence_threshold=Decimal("0.60"),
        )
        assert config.name == "Test"
        assert config.max_leverage == Decimal("3")
        assert config.stop_loss_pct == Decimal("0.02")


class TestBasePersona:
    def test_get_position_size_basic(self) -> None:
        class DummyPersona(BasePersona):
            @property
            def system_prompt(self) -> str:
                return "dummy"

            @property
            def voice(self) -> str:
                return "dummy voice"

        config = PersonaConfig(
            name="Dummy",
            risk_profile="moderate",
            description="Dummy for testing.",
            max_drawdown=Decimal("0.15"),
            preferred_timeframes=["15"],
            max_leverage=Decimal("2"),
            position_size_pct=Decimal("0.10"),
            stop_loss_pct=Decimal("0.02"),
            take_profit_pct=Decimal("0.05"),
            confidence_threshold=Decimal("0.70"),
        )
        persona = DummyPersona(config)
        capital = Decimal("10000")

        # signal_strength = 1.0 → 10% of capital * 2x leverage = 2000
        size = persona.get_position_size(capital, Decimal("1.0"))
        assert size == Decimal("2000")

    def test_get_position_size_respects_max_leverage(self) -> None:
        class DummyPersona(BasePersona):
            @property
            def system_prompt(self) -> str:
                return "dummy"

            @property
            def voice(self) -> str:
                return "dummy voice"

        config = PersonaConfig(
            name="Dummy",
            risk_profile="moderate",
            description="Dummy for testing.",
            max_drawdown=Decimal("0.15"),
            preferred_timeframes=["15"],
            max_leverage=Decimal("1"),  # no leverage
            position_size_pct=Decimal("0.20"),  # would be 2000 without cap
            stop_loss_pct=Decimal("0.02"),
            take_profit_pct=Decimal("0.05"),
            confidence_threshold=Decimal("0.70"),
        )
        persona = DummyPersona(config)
        capital = Decimal("10000")

        size = persona.get_position_size(capital, Decimal("1.0"))
        assert size == Decimal("2000")  # 20% of 10k at 1x leverage

    def test_get_position_size_clamps_signal(self) -> None:
        class DummyPersona(BasePersona):
            @property
            def system_prompt(self) -> str:
                return "dummy"

            @property
            def voice(self) -> str:
                return "dummy voice"

        config = PersonaConfig(
            name="Dummy",
            risk_profile="moderate",
            description="Dummy for testing.",
            max_drawdown=Decimal("0.15"),
            preferred_timeframes=["15"],
            max_leverage=Decimal("10"),
            position_size_pct=Decimal("0.10"),
            stop_loss_pct=Decimal("0.02"),
            take_profit_pct=Decimal("0.05"),
            confidence_threshold=Decimal("0.70"),
        )
        persona = DummyPersona(config)
        capital = Decimal("10000")

        # signal > 1 should be clamped to 1 → 10% * 10x = 10000
        size_high = persona.get_position_size(capital, Decimal("2.0"))
        assert size_high == Decimal("10000")

        # signal < 0 should be clamped to 0
        size_low = persona.get_position_size(capital, Decimal("-0.5"))
        assert size_low == Decimal("0")

    def test_format_market_context_includes_confidence(self) -> None:
        class DummyPersona(BasePersona):
            @property
            def system_prompt(self) -> str:
                return "Be smart."

            @property
            def voice(self) -> str:
                return "calm"

        config = PersonaConfig(
            name="Dummy",
            risk_profile="moderate",
            description="Dummy for testing.",
            max_drawdown=Decimal("0.15"),
            preferred_timeframes=["15"],
            max_leverage=Decimal("2"),
            position_size_pct=Decimal("0.10"),
            stop_loss_pct=Decimal("0.02"),
            take_profit_pct=Decimal("0.05"),
            confidence_threshold=Decimal("0.70"),
        )
        persona = DummyPersona(config)
        ctx = persona.format_market_context("price: 100", "rsi: 70")
        assert "Minimum confidence threshold: 0.70" in ctx
        assert "Be smart." in ctx
        assert "price: 100" in ctx


class TestAggressivePersona:
    def test_config(self) -> None:
        p = AggressivePersona()
        assert p.config.name == "Aggressive Momentum Hunter"
        assert p.config.risk_profile == "aggressive"
        assert p.config.max_drawdown == Decimal("0.25")
        assert p.config.max_leverage == Decimal("5")
        assert p.config.position_size_pct == Decimal("0.15")
        assert p.config.stop_loss_pct == Decimal("0.04")
        assert p.config.take_profit_pct == Decimal("0.12")
        assert p.config.confidence_threshold == Decimal("0.55")
        assert p.voice == "Alpha-seeking missile. Volatility is opportunity."
        assert "trend is your friend" in p.system_prompt


class TestConservativePersona:
    def test_config(self) -> None:
        p = ConservativePersona()
        assert p.config.name == "Conservative Value Seeker"
        assert p.config.risk_profile == "conservative"
        assert p.config.max_drawdown == Decimal("0.10")
        assert p.config.max_leverage == Decimal("1")
        assert p.config.position_size_pct == Decimal("0.05")
        assert p.config.stop_loss_pct == Decimal("0.015")
        assert p.config.take_profit_pct == Decimal("0.04")
        assert p.config.confidence_threshold == Decimal("0.75")
        assert p.voice == "Patient value hunter. Discipline over dopamine."
        assert "revert to the mean" in p.system_prompt


class TestSentimentPersona:
    def test_config(self) -> None:
        p = SentimentPersona()
        assert p.config.name == "Sentiment Oracle"
        assert p.config.risk_profile == "moderate"
        assert p.config.max_drawdown == Decimal("0.15")
        assert p.config.max_leverage == Decimal("2")
        assert p.config.position_size_pct == Decimal("0.10")
        assert p.config.stop_loss_pct == Decimal("0.025")
        assert p.config.take_profit_pct == Decimal("0.06")
        assert p.config.confidence_threshold == Decimal("0.65")
        assert p.voice == "Narrative navigator. Reading the crowd's mind."
        assert "market sentiment" in p.system_prompt


class TestArbitrageurPersona:
    def test_config(self) -> None:
        p = ArbitrageurPersona()
        assert p.config.name == "Arbitrage Hunter"
        assert p.config.risk_profile == "moderate"
        assert p.config.max_drawdown == Decimal("0.05")
        assert p.config.max_leverage == Decimal("1")
        assert p.config.position_size_pct == Decimal("0.20")
        assert p.config.stop_loss_pct == Decimal("0.005")
        assert p.config.take_profit_pct == Decimal("0.015")
        assert p.config.confidence_threshold == Decimal("0.80")
        assert p.voice == "Spread sniper. Inefficiency is my alpha."
        assert "price discrepancies" in p.system_prompt
