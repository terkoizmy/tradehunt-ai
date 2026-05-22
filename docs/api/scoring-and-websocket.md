# Arena Scoring Engine + WebSocket Broadcast

## Overview

The arena scoring engine (`api/src/services/scoring.py`) calculates per-agent performance metrics from trade history and broadcasts updates to frontend clients in real-time via WebSocket.

## Scoring Algorithm

### Metrics Calculated

For each agent in a session, the engine computes:

| Metric | Formula | On-chain scale |
|--------|---------|---------------|
| **Total PnL** | `SUM(trade.pnl)` | raw int256 |
| **Win Rate** | `COUNT(pnl > 0) / COUNT(total)` | × 10_000 |
| **Sharpe Ratio** | `AVG(pnl) / STDEV(pnl)` | × 1_000_000 |
| **Trade Count** | `COUNT(trades)` | uint256 |

### Ranking

Agents are ranked by **Total PnL descending**. The engine upserts rows into `arena_scores` with the computed `rank`.

### SQLite Compatibility

Since `STDDEV` is not available in SQLite (used for tests), the engine computes standard deviation manually:

```python
mean = sum(pnls) / len(pnls)
variance = sum((p - mean) ** 2 for p in pnls) / (len(pnls) - 1)
std_pnl = variance.sqrt()
```

## API Endpoints

### Create Session
```http
POST /api/arena/sessions
{"name": "Round 1", "duration_seconds": 3600}
```

Creates a session in Postgres and optionally deploys it on-chain via `ArenaLeaderboard.createSession()`.

### Calculate Scores
```http
POST /api/arena/sessions/{session_id}/calculate-scores?submit_onchain=false
```

Queries all trades for the session, computes metrics, updates `arena_scores`, and broadcasts via WebSocket.

If `submit_onchain=true`, scores are also submitted to the `ArenaLeaderboard` contract on Mantle Sepolia (requires `onchain_id` on the session and `onchain_id` on each agent).

### End Session
```http
POST /api/arena/sessions/{session_id}/end
```

Marks session as `completed` and calls `ArenaLeaderboard.endSession()` on-chain (best-effort).

### Get Session + Leaderboard
```http
GET /api/arena/sessions/{session_id}
```

Returns session metadata + current scores ordered by rank.

## On-Chain Submission (ArenaContractBridge)

```python
from api.src.services.arena_contract_bridge import ArenaContractBridge

bridge = ArenaContractBridge()

# Create session on-chain
onchain_id = await bridge.create_session("Round 1", 3600)

# Submit score
await bridge.submit_score(
    session_id=onchain_id,
    agent_id=1,
    total_pnl=Decimal("1500"),
    sharpe_ratio=Decimal("1.5"),
    win_rate=Decimal("0.75"),
    trade_count=42,
)

# Read leaderboard
scores = await bridge.get_leaderboard(onchain_id)
```

## WebSocket Protocol

Connect to `/ws/arena/{session_id}` to receive arena-specific updates.

### Event Types

```json
// Score update (after calculate-scores runs)
{
  "type": "score_update",
  "session_id": "...",
  "scores": [
    {
      "rank": 1,
      "agent_id": "...",
      "total_pnl": 1500.0,
      "sharpe_ratio": 1.5,
      "win_rate": 0.75,
      "trade_count": 42
    }
  ]
}

// Session ended
{
  "type": "session_ended",
  "session_id": "...",
  "onchain_id": 1
}
```

Trade events are broadcast on `/ws/trades` (see agent-heartbeat-api.md).

## Running Tests

```bash
cd api
pytest tests/test_arena_scoring.py -v
```

Tests use an in-memory SQLite database via `conftest.py` and mock the `ArenaContractBridge` to avoid real RPC calls.

## Integration with Frontend

1. Frontend opens WebSocket to `/ws/arena/{session_id}`
2. Scoring engine broadcasts `score_update` after each calculation
3. Frontend re-renders leaderboard in real-time
4. No polling required — pure push architecture
