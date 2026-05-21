"""Position sizing and risk management for agent trades."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RiskConfig:
    max_position_pct: Decimal = Decimal("0.1")  # 10% of capital per position
    max_daily_loss_pct: Decimal = Decimal("0.05")  # 5% daily loss limit
    stop_loss_pct: Decimal = Decimal("0.02")  # 2% stop loss
    take_profit_pct: Decimal = Decimal("0.04")  # 4% take profit
    max_open_positions: int = 3
    min_confidence: Decimal = Decimal("0.6")  # minimum LLM confidence


@dataclass
class RiskDecision:
    allowed: bool
    position_size: Decimal
    stop_loss_price: Decimal | None
    take_profit_price: Decimal | None
    reason: str


class RiskManager:
    """Validates trade decisions against risk parameters."""

    def __init__(
        self,
        capital: Decimal,
        config: RiskConfig | None = None,
    ) -> None:
        self.capital = capital
        self.config = config or RiskConfig()
        self._daily_pnl = Decimal("0")
        self._open_positions: int = 0

    def evaluate(
        self,
        action: str,
        price: Decimal,
        confidence: Decimal,
        side: str,
    ) -> RiskDecision:
        if action == "hold":
            return RiskDecision(
                allowed=True,
                position_size=Decimal("0"),
                stop_loss_price=None,
                take_profit_price=None,
                reason="Hold — no action needed",
            )

        if confidence < self.config.min_confidence:
            return RiskDecision(
                allowed=False,
                position_size=Decimal("0"),
                stop_loss_price=None,
                take_profit_price=None,
                reason=f"Confidence {confidence} below minimum {self.config.min_confidence}",
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

        position_size = self.capital * self.config.max_position_pct
        stop_loss = (
            price * (Decimal("1") - self.config.stop_loss_pct)
            if side == "buy"
            else price * (Decimal("1") + self.config.stop_loss_pct)
        )
        take_profit = (
            price * (Decimal("1") + self.config.take_profit_pct)
            if side == "buy"
            else price * (Decimal("1") - self.config.take_profit_pct)
        )

        self._open_positions += 1
        return RiskDecision(
            allowed=True,
            position_size=position_size,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            reason="Trade approved",
        )

    def update_pnl(self, pnl: Decimal) -> None:
        self._daily_pnl += pnl

    def close_position(self) -> None:
        self._open_positions = max(0, self._open_positions - 1)

    def reset_daily(self) -> None:
        self._daily_pnl = Decimal("0")
