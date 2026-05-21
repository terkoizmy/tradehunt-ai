"""MCP Bybit integration — optional enriched data access layer.

Provides structured market context for the LLM persona beyond raw pybit data.
Used as a supplement when deeper market analysis is needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class MCPMarketContext:
    symbol: str
    trend: str  # bullish / bearish / neutral
    volatility: str  # high / medium / low
    volume_profile: str  # increasing / decreasing / stable
    key_levels: list[Decimal]
    summary: str


class BybitMCP:
    """Optional MCP layer for enriched Bybit market data.

    When MCP tools are configured in the environment, this class
    provides structured market context that the LLM can reason about
    more effectively than raw orderbook snapshots.
    """

    def __init__(self) -> None:
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def analyze_market(
        self,
        symbol: str,
        orderbook: dict[str, Any] | None = None,
        klines: list[dict] | None = None,
    ) -> MCPMarketContext:
        """Produce structured market context from raw data.

        Falls back to basic analysis if MCP tools are not available.
        """
        trend = self._detect_trend(klines or [])
        volatility = self._detect_volatility(klines or [])
        volume_profile = self._detect_volume_profile(klines or [])
        key_levels = self._find_key_levels(orderbook or {})

        return MCPMarketContext(
            symbol=symbol,
            trend=trend,
            volatility=volatility,
            volume_profile=volume_profile,
            key_levels=key_levels,
            summary=(
                f"{symbol}: {trend} trend, {volatility} volatility, "
                f"volume {volume_profile}"
            ),
        )

    def _detect_trend(self, klines: list[dict]) -> str:
        if len(klines) < 10:
            return "neutral"
        closes = [Decimal(k[4]) for k in klines[:10]]
        if closes[0] > closes[-1] * Decimal("1.02"):
            return "bullish"
        elif closes[0] < closes[-1] * Decimal("0.98"):
            return "bearish"
        return "neutral"

    def _detect_volatility(self, klines: list[dict]) -> str:
        if len(klines) < 10:
            return "medium"
        highs = [Decimal(k[2]) for k in klines[:10]]
        lows = [Decimal(k[3]) for k in klines[:10]]
        avg_range = sum(h - l for h, l in zip(highs, lows)) / len(highs)
        avg_price = sum(highs + lows) / (len(highs) * 2)
        ratio = avg_range / avg_price if avg_price > 0 else Decimal("0")
        if ratio > Decimal("0.03"):
            return "high"
        elif ratio < Decimal("0.01"):
            return "low"
        return "medium"

    def _detect_volume_profile(self, klines: list[dict]) -> str:
        if len(klines) < 10:
            return "stable"
        recent_vol = sum(Decimal(k[5]) for k in klines[:5])
        older_vol = sum(Decimal(k[5]) for k in klines[5:10])
        if older_vol == 0:
            return "stable"
        ratio = recent_vol / older_vol
        if ratio > Decimal("1.2"):
            return "increasing"
        elif ratio < Decimal("0.8"):
            return "decreasing"
        return "stable"

    def _find_key_levels(self, orderbook: dict[str, Any]) -> list[Decimal]:
        # Simplified — in production, would analyze orderbook depth
        return []
