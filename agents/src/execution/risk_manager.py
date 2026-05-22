"""Position sizing and risk management for agent trades."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from agents.src.personas.base import BasePersona


@dataclass
class RiskConfig:
    """Global risk overrides. Persona-specific fields (SL%, TP%, confidence, leverage,
    position size) are read from the persona itself."""

    max_daily_loss_pct: Decimal = Decimal("0.05")  # 5% of capital daily loss limit
    max_open_positions: int = 3


@dataclass
class RiskDecision:
    allowed: bool
    position_size: Decimal
    stop_loss_price: Decimal | None
    take_profit_price: Decimal | None
    reason: str


class RiskManager:
    """Validates trade decisions against persona risk parameters and global limits."""

    def __init__(
        self,
        persona: BasePersona,
        capital: Decimal,
        config: RiskConfig | None = None,
    ) -> None:
        self.persona = persona
        self.capital = capital
        self.config = config or RiskConfig()
        self._daily_pnl = Decimal("0")
        self._open_positions = 0

    def evaluate(
        self,
        action: str,
        price: Decimal,
        confidence: Decimal,
        signal_strength: Decimal = Decimal("1.0"),
    ) -> RiskDecision:
        """Evaluate a trade decision against all risk rules.

        Args:
            action: "buy", "sell", or "hold"
            price: current market price
            confidence: LLM confidence in the decision
            signal_strength: strategy signal confidence (0–1)
        """
        if action == "hold":
            return RiskDecision(
                allowed=True,
                position_size=Decimal("0"),
                stop_loss_price=None,
                take_profit_price=None,
                reason="Hold — no action needed",
            )

        if confidence < self.persona.config.confidence_threshold:
            return RiskDecision(
                allowed=False,
                position_size=Decimal("0"),
                stop_loss_price=None,
                take_profit_price=None,
                reason=(
                    f"Confidence {confidence:.2f} below persona threshold "
                    f"{self.persona.config.confidence_threshold}"
                ),
            )

        if self._open_positions >= self.config.max_open_positions:
            return RiskDecision(
                allowed=False,
                position_size=Decimal("0"),
                stop_loss_price=None,
                take_profit_price=None,
                reason=f"Max open positions ({self.config.max_open_positions}) reached",
            )

        if self._daily_pnl < -self.capital * self.config.max_daily_loss_pct:
            return RiskDecision(
                allowed=False,
                position_size=Decimal("0"),
                stop_loss_price=None,
                take_profit_price=None,
                reason="Daily loss limit reached",
            )

        position_size = self.persona.get_position_size(self.capital, signal_strength)
        stop_loss = (
            price * (Decimal("1") - self.persona.config.stop_loss_pct)
            if action == "buy"
            else price * (Decimal("1") + self.persona.config.stop_loss_pct)
        )
        take_profit = (
            price * (Decimal("1") + self.persona.config.take_profit_pct)
            if action == "buy"
            else price * (Decimal("1") - self.persona.config.take_profit_pct)
        )

        return RiskDecision(
            allowed=True,
            position_size=position_size,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            reason="Trade approved",
        )

    def update_pnl(self, pnl: Decimal) -> None:
        """Record realized PnL from a closed trade."""
        self._daily_pnl += pnl

    def increment_open(self) -> None:
        """Call after a successful order execution."""
        self._open_positions += 1

    def decrement_open(self) -> None:
        """Call when a position is closed."""
        self._open_positions = max(0, self._open_positions - 1)

    def sync_open_positions(self, count: int) -> None:
        """Sync internal open-position count with external reality (e.g. Bybit API)."""
        self._open_positions = max(0, count)

    def reset_daily(self) -> None:
        """Reset daily PnL tracker (call at UTC midnight or on startup)."""
        self._daily_pnl = Decimal("0")
