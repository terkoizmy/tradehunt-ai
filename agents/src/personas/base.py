"""Base quant persona class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PersonaConfig:
    name: str
    risk_profile: str  # aggressive, moderate, conservative
    description: str
    max_drawdown: Decimal
    preferred_timeframes: list[str]
    max_leverage: Decimal
    position_size_pct: Decimal
    stop_loss_pct: Decimal
    take_profit_pct: Decimal
    confidence_threshold: Decimal


class BasePersona(ABC):
    """Abstract base for quant trading personas.

    Each persona shapes how the agent interprets market data and
    makes decisions. The persona system prompt is injected into
    the LLM call to give the agent a consistent "personality."
    """

    def __init__(self, config: PersonaConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt injected into LLM calls for this persona."""
        ...

    @property
    @abstractmethod
    def voice(self) -> str:
        """Short personality description for arena display."""
        ...

    def get_position_size(self, capital: Decimal, signal_strength: Decimal) -> Decimal:
        """Calculate position size based on risk profile and signal strength.

        Applies leverage as a multiplier on the margin allocation and clamps
        signal_strength to [0, 1].
        """
        clamped = max(Decimal("0"), min(Decimal("1"), signal_strength))
        margin = capital * self.config.position_size_pct * clamped
        return margin * self.config.max_leverage

    def format_market_context(self, market_data_str: str, signal_str: str) -> str:
        """Build the full prompt combining market data, signal, and persona."""
        return (
            f"You are a {self.config.name} quant trader. "
            f"Risk profile: {self.config.risk_profile}. "
            f"Max drawdown tolerance: {self.config.max_drawdown}. "
            f"Minimum confidence threshold: {self.config.confidence_threshold}.\n\n"
            f"### Persona\n{self.system_prompt}\n\n"
            f"### Market Data\n{market_data_str}\n\n"
            f"### Technical Signal\n{signal_str}\n\n"
            "Respond with a JSON object: "
            '{"action": "buy"|"sell"|"hold", '
            '"symbol": "string", '
            '"confidence": 0.0-1.0, '
            '"reasoning": "string"}'
        )
