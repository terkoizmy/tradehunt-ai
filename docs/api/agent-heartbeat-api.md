# Agent Heartbeat + Trade Reporting API

## Overview

The agent heartbeat and trade reporting API is the bridge between running AI agents and the tradehunt backend. Agents register on startup, send periodic heartbeats, report trades and decisions, and notify on shutdown.

## Authentication

All protected endpoints require the `X-API-Key` header matching the agent's API key.

```
X-API-Key: <api_key_returned_on_registration>
```

## Endpoints

### Register Agent
```http
POST /api/agents
```

Request:
```json
{
  "name": "Aggressive Hunter",
  "persona": "aggressive",
  "wallet_address": "0x...",
  "capital": 10000.0,
  "symbol": "BTCUSDT",
  "persona_config": { "risk_profile": "high", "max_leverage": 10 }
}
```

Response:
```json
{
  "agent_id": "uuid",
  "api_key": "secure-token",
  "name": "Aggressive Hunter",
  "persona": "aggressive",
  "status": "idle"
}
```

### Heartbeat
```http
POST /api/agents/{agent_id}/heartbeat
```

Updates `last_heartbeat` and sets status to `online`. Returns current status and timestamp.

### Report Trade
```http
POST /api/agents/{agent_id}/trades
```

Request:
```json
{
  "action": "buy",
  "symbol": "BTCUSDT",
  "side": "Buy",
  "price": 50000.0,
  "quantity": 0.001,
  "pnl": 150.0,
  "stop_loss": 48000.0,
  "take_profit": 55000.0,
  "confidence": 0.85,
  "reasoning": "Bullish crossover",
  "order_id": "ord-123",
  "executed_at": "2026-05-22T09:00:00Z"
}
```

### Report Decision
```http
POST /api/agents/{agent_id}/decisions
```

Request:
```json
{
  "action": "buy",
  "symbol": "BTCUSDT",
  "confidence": 0.85,
  "reasoning": "EMA crossover confirmed",
  "signal_action": "buy",
  "signal_confidence": 0.78,
  "risk_allowed": true
}
```

### Set Offline
```http
POST /api/agents/{agent_id}/offline
```

Sets agent status to `stopped`.

### List Agents
```http
GET /api/agents?persona=aggressive&status=online
```

### Get Agent Details
```http
GET /api/agents/{agent_id}
```

### Get Agent Trades
```http
GET /api/agents/{agent_id}/trades?limit=50
```

## Agent Status Lifecycle

| Status | Meaning | Transition |
|--------|---------|------------|
| `idle` | Just registered, no heartbeat yet | Registration |
| `online` | Heartbeat received within 90s | Heartbeat API |
| `idle` | No trades in 5+ minutes while online | Background task |
| `offline` | No heartbeat for 90s+ | Background task |
| `stopped` | Graceful shutdown | Offline API |

## Background Task

A background coroutine runs every 30 seconds:
1. Queries agents with status `online`
2. Marks `offline` if `last_heartbeat` is older than 90 seconds
3. Marks `idle` if `online` and no heartbeat in 5 minutes
4. Broadcasts status changes via WebSocket

## WebSocket Events

Connect to `/ws/trades` to receive real-time updates:

```json
// Agent status change
{"type": "agent_status", "agent_id": "...", "status": "online"}

// New trade
{"type": "trade", "agent_id": "...", "action": "buy", "symbol": "BTCUSDT", "price": 50000, "quantity": 0.001}

// New decision
{"type": "decision", "agent_id": "...", "action": "buy", "reasoning": "..."}

// Agent registered
{"type": "agent_registered", "agent_id": "...", "name": "...", "persona": "..."}
```

## Agent Integration

The `agents/src/api/client.py` module wraps all API calls:

```python
from agents.src.api.client import APIClient

api = APIClient(base_url="http://localhost:8000")
agent_id = await api.register(name="Hunter", persona="aggressive", ...)
await api.heartbeat()
await api.report_trade({"action": "buy", "symbol": "BTCUSDT", ...})
await api.report_decision({"action": "buy", "reasoning": "..."})
await api.set_offline()
```

Enable reporting from the CLI with:
```bash
python -m agents.src.main --persona aggressive --api-url http://localhost:8000
```

## Running Tests

```bash
cd api
pytest tests/test_agents_api.py -v
```

Tests use an in-memory SQLite database via `conftest.py` with the FastAPI app overridden to use the test DB session.
