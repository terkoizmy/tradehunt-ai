"""Integration tests for arena scoring + WebSocket broadcast (Issue #7)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from api.src.db.models import Agent, ArenaScore, ArenaSession, Trade


@pytest.fixture
async def session_with_trades(client: AsyncClient):
    """Create an arena session, an agent, and some trades."""
    # Mock on-chain bridge to avoid real RPC calls
    with patch("api.src.routes.arena.ArenaContractBridge") as MockBridge:
        MockBridge.return_value.create_session.return_value = 1
        # Create session
        resp = await client.post("/api/arena/sessions", json={
            "name": "Test Round",
            "duration_seconds": 3600,
        })
    assert resp.status_code == 200
    session_id = resp.json()["id"]

    # Register agent
    resp = await client.post("/api/agents", json={
        "name": "Scorer",
        "persona": "aggressive",
        "wallet_address": "0x1111111111111111111111111111111111111111",
        "capital": 10000.0,
        "symbol": "BTCUSDT",
    })
    assert resp.status_code == 200
    agent_id = resp.json()["agent_id"]
    api_key = resp.json()["api_key"]

    # Report trades
    for i, pnl in enumerate([100, -50, 200, 0, 150]):
        resp = await client.post(
            f"/api/agents/{agent_id}/trades",
            headers={"X-API-Key": api_key},
            json={
                "action": "buy",
                "symbol": "BTCUSDT",
                "side": "Buy",
                "price": 50000.0 + i,
                "quantity": 0.001,
                "pnl": pnl,
            },
        )
        assert resp.status_code == 200

    return session_id, agent_id


@pytest.mark.asyncio
async def test_calculate_scores(client: AsyncClient, session_with_trades):
    session_id, agent_id = session_with_trades

    resp = await client.post(f"/api/arena/sessions/{session_id}/calculate-scores")
    assert resp.status_code == 200
    data = resp.json()
    # Filter to the agent we created
    agent_scores = [s for s in data if s["agent_id"] == agent_id]
    assert len(agent_scores) == 1
    score = agent_scores[0]
    assert score["total_pnl"] == 400.0
    assert score["trade_count"] == 5
    assert score["win_rate"] == 0.6  # 3 out of 5 positive
    assert score["rank"] == 1


@pytest.mark.asyncio
async def test_end_session(client: AsyncClient, session_with_trades):
    session_id, _ = session_with_trades
    with patch("api.src.routes.arena.ArenaContractBridge") as MockBridge:
        MockBridge.return_value.end_session.return_value = "0xend"
        resp = await client.post(f"/api/arena/sessions/{session_id}/end")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["session_id"] == session_id
