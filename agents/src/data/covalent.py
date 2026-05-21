"""Covalent API on-chain data reader."""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import httpx


class CovalentClient:
    """Reads on-chain data from Mantle via Covalent API.

    Provides historical trade data, token balances, and transaction
    history for agents to incorporate on-chain context into decisions.
    """

    BASE_URL = "https://api.covalenthq.com/v1"

    def __init__(self) -> None:
        self._api_key = os.getenv("COVALENT_API_KEY", "")
        self._chain_id = "5003"  # Mantle Sepolia testnet

    async def get_token_balances(self, address: str) -> list[dict[str, Any]]:
        if not self._api_key:
            return []
        url = f"{self.BASE_URL}/{self._chain_id}/address/{address}/balances_v2/"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                params={"key": self._api_key},
            )
            if resp.status_code != 200:
                return []
            return resp.json().get("data", {}).get("items", [])

    async def get_transactions(self, address: str, limit: int = 50) -> list[dict[str, Any]]:
        if not self._api_key:
            return []
        url = f"{self.BASE_URL}/{self._chain_id}/address/{address}/transactions_v3/"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                params={"key": self._api_key, "pageSize": str(limit)},
            )
            if resp.status_code != 200:
                return []
            return resp.json().get("data", {}).get("items", [])
