"""Tests for risk manager and CLI integration."""

from decimal import Decimal

import pytest

from agents.src.execution.risk_manager import RiskConfig, RiskDecision, RiskManager
from agents.src.personas.aggressive import AggressivePersona
from agents.src.personas.conservative import ConservativePersona
from agents.src.personas.sentiment import SentimentPersona


class TestRiskManager:
    def test_hold_always_allowed(self) -> None:
        persona = ConservativePersona()
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        decision = risk.evaluate("hold", Decimal("50000"), Decimal("0.9"))
        assert decision.allowed is True
        assert decision.position_size == Decimal("0")
        assert "Hold" in decision.reason

    def test_confidence_below_persona_threshold(self) -> None:
        persona = ConservativePersona()  # threshold = 0.75
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        decision = risk.evaluate("buy", Decimal("50000"), Decimal("0.50"))
        assert decision.allowed is False
        assert "below persona threshold" in decision.reason

    def test_confidence_above_threshold_passes(self) -> None:
        persona = AggressivePersona()  # threshold = 0.55
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        decision = risk.evaluate("buy", Decimal("50000"), Decimal("0.80"))
        assert decision.allowed is True
        assert decision.position_size > 0

    def test_max_open_positions_blocks(self) -> None:
        persona = SentimentPersona()
        risk = RiskManager(
            persona=persona,
            capital=Decimal("10000"),
            config=RiskConfig(max_open_positions=2),
        )
        risk._open_positions = 2
        decision = risk.evaluate("buy", Decimal("50000"), Decimal("0.99"))
        assert decision.allowed is False
        assert "Max open positions" in decision.reason

    def test_daily_loss_limit_blocks(self) -> None:
        persona = AggressivePersona()
        risk = RiskManager(
            persona=persona,
            capital=Decimal("10000"),
            config=RiskConfig(max_daily_loss_pct=Decimal("0.05")),
        )
        risk.update_pnl(Decimal("-600"))  # exceeds 5% of 10k
        decision = risk.evaluate("buy", Decimal("50000"), Decimal("0.99"))
        assert decision.allowed is False
        assert "Daily loss limit" in decision.reason

    def test_position_size_uses_persona(self) -> None:
        persona = AggressivePersona()  # 15% position * 5x leverage
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        decision = risk.evaluate("buy", Decimal("50000"), Decimal("0.90"))
        assert decision.allowed is True
        # 10k * 0.15 * 1.0 * 5 = 7500
        assert decision.position_size == Decimal("7500")

    def test_stop_loss_and_take_profit_buy(self) -> None:
        persona = ConservativePersona()  # SL 1.5%, TP 4%
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        price = Decimal("50000")
        decision = risk.evaluate("buy", price, Decimal("0.99"))
        assert decision.stop_loss_price == price * (Decimal("1") - Decimal("0.015"))
        assert decision.take_profit_price == price * (Decimal("1") + Decimal("0.04"))

    def test_stop_loss_and_take_profit_sell(self) -> None:
        persona = ConservativePersona()  # SL 1.5%, TP 4%
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        price = Decimal("50000")
        decision = risk.evaluate("sell", price, Decimal("0.99"))
        assert decision.stop_loss_price == price * (Decimal("1") + Decimal("0.015"))
        assert decision.take_profit_price == price * (Decimal("1") - Decimal("0.04"))

    def test_signal_strength_scales_position(self) -> None:
        persona = AggressivePersona()
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        full = risk.evaluate("buy", Decimal("50000"), Decimal("0.90"), Decimal("1.0"))
        half = risk.evaluate("buy", Decimal("50000"), Decimal("0.90"), Decimal("0.5"))
        assert half.position_size == full.position_size / 2

    def test_increment_and_decrement_open(self) -> None:
        persona = AggressivePersona()
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        assert risk._open_positions == 0
        risk.increment_open()
        assert risk._open_positions == 1
        risk.decrement_open()
        assert risk._open_positions == 0
        risk.decrement_open()  # should not go below 0
        assert risk._open_positions == 0

    def test_sync_open_positions(self) -> None:
        persona = AggressivePersona()
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        risk.sync_open_positions(5)
        assert risk._open_positions == 5
        risk.sync_open_positions(-1)
        assert risk._open_positions == 0

    def test_reset_daily(self) -> None:
        persona = AggressivePersona()
        risk = RiskManager(persona=persona, capital=Decimal("10000"))
        risk.update_pnl(Decimal("-500"))
        assert risk._daily_pnl < 0
        risk.reset_daily()
        assert risk._daily_pnl == Decimal("0")
