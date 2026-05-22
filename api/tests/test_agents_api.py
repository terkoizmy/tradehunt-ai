"""Tests for agent heartbeat + trade reporting API (Issue #19)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from api.src.db.database import async_session
from api.src.db.models import Agent, Decision, Trade


@pytest.fixture
async def registered_agent(client: AsyncClient):
    """Register an agent and return (agent_id, api_key)."""
    resp = await client.post("/api/agents", json={
        "name": "Test Hunter",
        "persona": "aggressive",
        "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
        "capital": 10000.0,
        "symbol": "BTCUSDT",
    })
    assert resp.status_code == 200
    data = resp.json()
    return data["agent_id"], data["api_key"]


@pytest.mark.asyncio
async def test_register_agent(client: AsyncClient):
    resp = await client.post("/api/agents", json={
        "name": "Alpha",
        "persona": "conservative",
        "wallet_address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "capital": 5000.0,
        "symbol": "ETHUSDT",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "agent_id" in data
    assert "api_key" in data
    assert data["name"] == "Alpha"
    assert data["persona"] == "conservative"
    assert data["status"] == "idle"


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, registered_agent):
    agent_id, _ = registered_agent
    resp = await client.get("/api/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert any(a["id"] == agent_id for a in data)


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient, registered_agent):
    agent_id, _ = registered_agent
    resp = await client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == agent_id
    assert data["name"] == "Test Hunter"


@pytest.mark.asyncio
async def test_heartbeat(client: AsyncClient, registered_agent):
    agent_id, api_key = registered_agent
    resp = await client.post(
        f"/api/agents/{agent_id}/heartbeat",
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_heartbeat_rejects_wrong_key(client: AsyncClient, registered_agent):
    agent_id, _ = registered_agent
    resp = await client.post(
        f"/api/agents/{agent_id}/heartbeat",
        headers={"X-API-Key": "invalid-key"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_report_trade(client: AsyncClient, registered_agent):
    agent_id, api_key = registered_agent
    resp = await client.post(
        f"/api/agents/{agent_id}/trades",
        headers={"X-API-Key": api_key},
        json={
            "action": "buy",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "price": 50000.0,
            "quantity": 0.001,
            "pnl": 150.0,
            "confidence": 0.85,
            "reasoning": "Bullish crossover",
            "order_id": "ord-123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "buy"
    assert data["symbol"] == "BTCUSDT"
    assert data["pnl"] == 150.0


@pytest.mark.asyncio
async def test_get_agent_trades(client: AsyncClient, registered_agent):
    agent_id, api_key = registered_agent
    await client.post(
        f"/api/agents/{agent_id}/trades",
        headers={"X-API-Key": api_key},
        json={
            "action": "buy",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "price": 50000.0,
            "quantity": 0.001,
        },
    )
    resp = await client.get(f"/api/agents/{agent_id}/trades")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_report_decision(client: AsyncClient, registered_agent):
    agent_id, api_key = registered_agent
    resp = await client.post(
        f"/api/agents/{agent_id}/decisions",
        headers={"X-API-Key": api_key},
        json={
            "action": "buy",
            "symbol": "BTCUSDT",
            "confidence": 0.85,
            "reasoning": "EMA crossover confirmed",
            "signal_action": "buy",
            "signal_confidence": 0.78,
            "risk_allowed": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "recorded"
    assert "id" in data


@pytest.mark.asyncio
async def test_set_offline(client: AsyncClient, registered_agent):
    agent_id, api_key = registered_agent
    resp = await client.post(
        f"/api/agents/{agent_id}/offline",
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stopped"
    assert data["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_trade_requires_auth(client: AsyncClient, registered_agent):
    agent_id, _ = registered_agent
    resp = await client.post(
        f"/api/agents/{agent_id}/trades",
        json={"action": "buy", "symbol": "BTCUSDT", "side": "Buy", "price": 1.0, "quantity": 1.0},
    )
    assert resp.status_code == 422  # missing X-API-Key header
