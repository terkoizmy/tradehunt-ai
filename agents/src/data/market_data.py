"""Unified market data model combining Bybit + Pyth + on-chain data."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from agents.src.execution.bybit_mcp import MCPMarketContext


@dataclass
class Signal:
    action: str  # buy, sell, hold
    symbol: str
    confidence: Decimal
    price: Decimal
    reasoning: str
    metadata: dict = field(default_factory=dict)


@dataclass
class MarketData:
    symbol: str
    last_price: Decimal
    bid: Decimal
    ask: Decimal
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    klines: list[dict] = field(default_factory=list)
    mcp_context: MCPMarketContext | None = None

    def to_context_string(self) -> str:
        """Format market data as a string for the LLM prompt."""
        parts = [
            f"Symbol: {self.symbol}",
            f"Price: {self.last_price}",
            f"Bid/Ask: {self.bid} / {self.ask}",
            f"24h Volume: {self.volume_24h}",
            f"24h Range: {self.low_24h} - {self.high_24h}",
        ]
        if self.mcp_context:
            parts.append(f"Market Analysis: {self.mcp_context.summary}")
        return "\n".join(parts)
