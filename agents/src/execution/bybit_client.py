"""Bybit testnet client wrapper around pybit v5.16.0."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from pybit.unified_trading import HTTP, WebSocket


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    price: Decimal
    quantity: Decimal
    success: bool
    error: str | None = None


@dataclass
class MarketSnapshot:
    symbol: str
    bid: Decimal
    ask: Decimal
    last_price: Decimal
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal


class BybitClient:
    """Async-friendly wrapper around pybit for Bybit testnet."""

    def __init__(self) -> None:
        self._api_key = os.getenv("BYBIT_API_KEY", "")
        self._api_secret = os.getenv("BYBIT_API_SECRET", "")
        self._testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"

        if not self._api_key or not self._api_secret:
            raise ValueError(
                "BYBIT_API_KEY and BYBIT_API_SECRET must be set in .env"
            )

        self._http: Optional[HTTP] = None
        self._ws: Optional[WebSocket] = None

    @property
    def http(self) -> HTTP:
        if self._http is None:
            self._http = HTTP(
                testnet=self._testnet,
                api_key=self._api_key,
                api_secret=self._api_secret,
            )
        return self._http

    @property
    def ws(self) -> WebSocket:
        if self._ws is None:
            self._ws = WebSocket(
                testnet=self._testnet,
                channel_type="linear",
            )
        return self._ws

    def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        ticker = self.http.get_tickers(category="linear", symbol=symbol)
        data = ticker["result"]["list"][0]
        return MarketSnapshot(
            symbol=symbol,
            bid=Decimal(data["bid1Price"]),
            ask=Decimal(data["ask1Price"]),
            last_price=Decimal(data["lastPrice"]),
            volume_24h=Decimal(data["volume24h"]),
            high_24h=Decimal(data["highPrice24h"]),
            low_24h=Decimal(data["lowPrice24h"]),
        )

    def get_klines(
        self, symbol: str, interval: str = "15", limit: int = 100
    ) -> list[dict]:
        result = self.http.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
        return result["result"]["list"]

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: str,
        order_type: str = "Market",
        price: str | None = None,
        stop_loss: str | None = None,
        take_profit: str | None = None,
    ) -> OrderResult:
        try:
            result = self.http.place_order(
                category="linear",
                symbol=symbol,
                side=side.capitalize(),
                orderType=order_type,
                qty=qty,
                price=price,
                stopLoss=stop_loss,
                takeProfit=take_profit,
            )
            if result["retCode"] != 0:
                return OrderResult(
                    order_id="",
                    symbol=symbol,
                    side=side,
                    price=Decimal(price or "0"),
                    quantity=Decimal(qty),
                    success=False,
                    error=result["retMsg"],
                )
            return OrderResult(
                order_id=result["result"]["orderId"],
                symbol=symbol,
                side=side,
                price=Decimal(price or "0"),
                quantity=Decimal(qty),
                success=True,
            )
        except Exception as e:
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                price=Decimal(price or "0"),
                quantity=Decimal(qty),
                success=False,
                error=str(e),
            )

    def get_positions(self, symbol: str | None = None) -> list[dict]:
        params = {"category": "linear"}
        if symbol:
            params["symbol"] = symbol
        result = self.http.get_positions(**params)
        return result["result"]["list"]

    def get_closed_pnl(
        self,
        symbol: str,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch recently closed PnL records for a symbol."""
        result = self.http.get_closed_pnl(
            category="linear",
            symbol=symbol,
            limit=limit,
        )
        return result["result"]["list"]

    def close(self) -> None:
        if self._ws is not None:
            self._ws.exit()
