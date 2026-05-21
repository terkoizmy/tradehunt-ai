"""LLM decision engine using Ollama Cloud API."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

import httpx


class DecisionEngine:
    """Sends market context + persona prompt to Ollama Cloud API.

    Returns structured JSON with trade decision, confidence, and reasoning.
    """

    def __init__(self) -> None:
        self._api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self._api_key = os.getenv("OLLAMA_API_KEY", "")
        self._model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    async def decide(
        self,
        persona_prompt: str,
        market_context: str,
        signal_text: str,
    ) -> dict[str, Any]:
        """Get trading decision from the LLM persona."""
        full_prompt = (
            f"{persona_prompt}\n\n"
            f"### Market Data\n{market_context}\n\n"
            f"### Technical Signal\n{signal_text}\n\n"
            'Respond ONLY with a JSON object (no markdown, no explanation):\n'
            '{"action": "buy"|"sell"|"hold", "symbol": "string", '
            '"confidence": 0.0-1.0, "reasoning": "string"}'
        )

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "You are a quant trading agent. Respond only with valid JSON."},
                {"role": "user", "content": full_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "top_p": 0.9},
        }

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
                return self._parse_response(content)
            except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
                return {
                    "action": "hold",
                    "symbol": "",
                    "confidence": 0.0,
                    "reasoning": f"LLM error: {e}",
                }

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse LLM response, handling markdown code blocks."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(content)
