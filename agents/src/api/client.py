"""HTTP client for agents to report to the tradehunt backend API."""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any

import httpx

logger = logging.getLogger("tradehunt.api")

DEFAULT_BASE_URL = "http://localhost:8000"


class APIClient:
    """Wraps REST calls to the tradehunt backend."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("TRADEHUNT_API_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.getenv("TRADEHUNT_API_KEY", "")
        self.agent_id: str | None = None
        self._client = httpx.AsyncClient(timeout=30.0)

    # ─── Registration ────────────────────────────────────────────────────────

    async def register(
        self,
        name: str,
        persona: str,
        wallet_address: str,
        capital: Decimal,
        symbol: str,
        persona_config: dict[str, Any] | None = None,
    ) -> str:
        """Register agent with the backend. Returns agent_id."""
        payload = {
            "name": name,
            "persona": persona,
            "wallet_address": wallet_address,
            "capital": float(capital),
            "symbol": symbol,
        }
        if persona_config:
            payload["persona_config"] = persona_config

        resp = await self._client.post(f"{self.base_url}/api/agents", json=payload)
        resp.raise_for_status()
        data = resp.json()
        self.agent_id = data["agent_id"]
        self.api_key = data["api_key"]
        logger.info("Registered agent %s with API key", self.agent_id)
        return self.agent_id

    # ─── Heartbeat ───────────────────────────────────────────────────────────

    async def heartbeat(self) -> None:
        """Send a heartbeat ping to the backend."""
        if not self.agent_id or not self.api_key:
            logger.warning("Cannot heartbeat: agent not registered")
            return
        resp = await self._client.post(
            f"{self.base_url}/api/agents/{self.agent_id}/heartbeat",
            headers={"X-API-Key": self.api_key},
        )
        resp.raise_for_status()

    # ─── Trade reporting ─────────────────────────────────────────────────────

    async def report_trade(self, trade: dict[str, Any]) -> None:
        """Report a completed trade to the backend."""
        if not self.agent_id or not self.api_key:
            logger.warning("Cannot report trade: agent not registered")
            return
        resp = await self._client.post(
            f"{self.base_url}/api/agents/{self.agent_id}/trades",
            headers={"X-API-Key": self.api_key},
            json=trade,
        )
        resp.raise_for_status()

    # ─── Decision reporting ──────────────────────────────────────────────────

    async def report_decision(self, decision: dict[str, Any]) -> None:
        """Report an LLM decision to the backend."""
        if not self.agent_id or not self.api_key:
            logger.warning("Cannot report decision: agent not registered")
            return
        resp = await self._client.post(
            f"{self.base_url}/api/agents/{self.agent_id}/decisions",
            headers={"X-API-Key": self.api_key},
            json=decision,
        )
        resp.raise_for_status()

    # ─── Offline ─────────────────────────────────────────────────────────────

    async def set_offline(self) -> None:
        """Notify the backend that the agent is shutting down."""
        if not self.agent_id or not self.api_key:
            logger.warning("Cannot set offline: agent not registered")
            return
        resp = await self._client.post(
            f"{self.base_url}/api/agents/{self.agent_id}/offline",
            headers={"X-API-Key": self.api_key},
        )
        resp.raise_for_status()
        logger.info("Agent %s marked offline", self.agent_id)

    # ─── Cleanup ─────────────────────────────────────────────────────────────

    async def close(self) -> None:
        await self._client.aclose()
