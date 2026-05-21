"""Pyth Network oracle price feed reader."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PythPrice:
    symbol: str
    price: Decimal
    confidence: Decimal
    timestamp: int


class PythFeed:
    """Reads price data from Pyth Network on Mantle.

    Pyth provides 80+ verified price feeds on Mantle Sepolia.
    This class reads the on-chain price data via the Pyth contract.
    """

    PYTH_CONTRACT = "0xA2aa501b19aff244D90cc15a4Cf739D2725B5729"  # Mantle Sepolia

    def __init__(self, web3_client=None) -> None:
        self._w3 = web3_client
        self._price_feeds: dict[str, str] = {
            "BTC/USD": "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
            "ETH/USD": "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
        }

    def get_price(self, symbol: str) -> PythPrice | None:
        """Read current price for a symbol from the Pyth oracle."""
        feed_id = self._price_feeds.get(symbol)
        if feed_id is None:
            return None
        # In production: call Pyth contract getPrice(feed_id)
        # For now, stub returning placeholder
        return None

    def get_prices(self, symbols: list[str]) -> dict[str, PythPrice | None]:
        return {s: self.get_price(s) for s in symbols}
