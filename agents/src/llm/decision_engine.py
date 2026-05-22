"""LLM decision engine using Ollama Cloud API."""

from __future__ import annotations

import asyncio
import json
import os
from decimal import Decimal
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from agents.src.data.market_data import Signal


class TradeDecision(BaseModel):
    """Validated LLM trading decision."""

    action: str = Field(..., pattern=r"^(buy|sell|hold)$")
    symbol: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, v: Any) -> float:
        return float(v)


class DecisionEngine:
    """Sends market context + persona prompt to Ollama Cloud API.

    Returns structured JSON with trade decision, confidence, and reasoning.
    """

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        self._api_url = (api_url or os.getenv("OLLAMA_API_URL", "http://localhost:11434")).rstrip("/")
        self._api_key = api_key or os.getenv("OLLAMA_API_KEY", "")
        self._model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def decide(
        self,
        persona_prompt: str,
        market_context: str,
        signal_text: str,
    ) -> dict[str, Any]:
        """Get trading decision from the LLM persona with retries.

        The persona prompt is sent as the system message so the model
        adopts the quant personality before reasoning about market data.
        """
        user_prompt = (
            f"### Market Data\n{market_context}\n\n"
            f"### Technical Signal\n{signal_text}\n\n"
            "Respond ONLY with a JSON object (no markdown, no explanation):\n"
            '{"action": "buy"|"sell"|"hold", "symbol": "string", '
            '"confidence": 0.0-1.0, "reasoning": "string"}'
        )

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": persona_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "top_p": 0.9},
        }

        for attempt in range(1, self.max_retries + 1):
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    resp = await client.post(
                        f"{self._api_url}/api/chat",
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["message"]["content"]
                    return self._parse_and_validate(content)
                except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** (attempt - 1))
                        await asyncio.sleep(delay)
                        continue
                    return self._error_response(f"HTTP error after {self.max_retries} retries: {e}")
                except (KeyError, json.JSONDecodeError) as e:
                    return self._error_response(f"Parse error: {e}")

        return self._error_response("Exhausted retries")

    async def decide_with_threshold(
        self,
        persona_prompt: str,
        market_context: str,
        signal: Signal,
        confidence_threshold: Decimal,
    ) -> dict[str, Any]:
        """Decide and enforce a minimum confidence threshold."""
        signal_text = (
            f"Action: {signal.action}, Confidence: {signal.confidence}, "
            f"Reasoning: {signal.reasoning}"
        )
        decision = await self.decide(persona_prompt, market_context, signal_text)
        if decision["action"] in ("buy", "sell"):
            dec_conf = Decimal(str(decision.get("confidence", 0)))
            if dec_conf < confidence_threshold:
                return {
                    "action": "hold",
                    "symbol": decision.get("symbol", ""),
                    "confidence": float(dec_conf),
                    "reasoning": (
                        f"Confidence {dec_conf} below threshold {confidence_threshold}. "
                        f"Original: {decision.get('reasoning', '')}"
                    ),
                }
        return decision

    def _parse_and_validate(self, content: str) -> dict[str, Any]:
        """Parse LLM response, strip markdown, validate with Pydantic."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            raw = json.loads(content)
            decision = TradeDecision.model_validate(raw)
            return decision.model_dump()
        except (json.JSONDecodeError, Exception) as e:
            return self._error_response(f"Validation error: {e}")

    def _error_response(self, reason: str) -> dict[str, Any]:
        return {
            "action": "hold",
            "symbol": "",
            "confidence": 0.0,
            "reasoning": reason,
        }
