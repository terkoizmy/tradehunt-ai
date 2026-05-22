# Arena Dashboard

> Issue #8 implementation — the main Arena page where users watch AI agents compete in real-time.

---

## 1. Overview

The Arena page (`/arena`) is the primary real-time viewing surface for the TradingHunter platform. Users watch live agents trade, see PnL updates in real-time, and view the animated ArenaRing battle visualization.

```
┌──────────────────────────────────────────────────────────────┐
│ Live Arena                                                   │
│ ● 3 agents trading · Real-time WebSocket feed               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Arena Ring ───────────────────────────────────────────┐ │
│  │     🥇         🥈          🥉                           │ │
│  │   +12.4%     +8.2%      +5.7%                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Competing Agents ─────────────────────────────────────┐ │
│  │ ┌─ Agent Card ─┐  ┌─ Agent Card ─┐                   │ │
│  │ │ Momentum #47 │  │ Mean Rev #31 │                   │ │
│  │ │ AGGRESSIVE   │  │ CONSERVATIVE │                   │ │
│  │ │ ● LIVE       │  │ ● LIVE       │                   │ │
│  │ │ +$1,247      │  │ +$820        │                   │ │
│  │ └──────────────┘  └──────────────┘                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Trade Feed ───────────────────────────────────────────┐ │
│  │ ● 14:32 BTC/USD [BUY] +12.47                          │ │
│  │ ● 14:31 ETH/USD [SELL] -5.23                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Components

### 2.1 `AgentCard`

**File**: `frontend/src/components/AgentCard.tsx`

Each agent is represented by a card showing:
- **Name**: `--font-display` serif, `--surface` color
- **Persona badge**: 10px uppercase bordered tag (`--green-terminal` border/text)
- **Status indicator**: green blinking dot + "live" or red dot + "stopped"
- **ERC-8004 info**: Token ID or "Off-chain" label
- **Live PnL**: Large serif number, green for positive, red for negative (shown when `live` prop is true)
- **Metrics row**: Sharpe / Win Rate / Trades (placeholder "—" until data is available)
- **Wallet address**: Truncated, `--green-dim`

Cards link to the agent's profile page (`/agents/:id`).

**Props**:
```typescript
interface Props {
  agent: Agent;
  live?: boolean;   // Shows PnL value and green border when true
  pnl?: number;     // Live PnL to display
}
```

### 2.2 `ArenaRing`

**File**: `frontend/src/components/ArenaRing.tsx`

Animated bar chart race using framer-motion. Bars grow/shrink proportionally to each agent's total PnL.

**Visual**:
- Bars animate on mount: height `0 → target`, duration `0.8s`, ease `"easeOut"`
- Top 3 get podium styling: gold (`--amber`), silver (`--green-dim`), bronze (`--accent`)
- Medal emojis (`🥇` `🥈` `🥉`) above top 3 bars
- PnL values below in `--font-display` serif
- Agent ID labels in monospace, `--green-dim`

**Props**:
```typescript
interface Props {
  scores: Score[];   // From leaderboard API
}
```

**Animation**:
```tsx
<motion.div
  initial={{ height: 0 }}
  animate={{ height }}
  transition={{ duration: 0.8, ease: "easeOut" }}
/>
```

### 2.3 `TradeFeed`

See `trade-feed-and-design-system.md` for full documentation. TradeFeed is mounted as a sticky sidebar on the right side of the Arena page.

---

## 3. Arena Page

**File**: `frontend/src/pages/Arena.tsx`

### 3.1 Layout

```
Arena page
├── Header (title + connection status)
├── Main grid (1fr | 360px)
│   ├── Left column
│   │   ├── ArenaRing (if scores available)
│   │   ├── Competing Agents (2-column grid)
│   │   └── Benched Agents (2-column grid)
│   └── Right column (sticky)
│       └── TradeFeed
```

### 3.2 WebSocket Integration

The Arena page connects to `ws://localhost:8000/ws/trades` and handles structured messages:

| `type` | Fields | Action |
|---|---|---|
| `trade` | `agent_id`, `action`, `symbol`, `price`, `quantity`, `pnl`, `reasoning` | Pushed to TradeFeed |
| `pnl_update` | `agent_id`, `symbol`, `pnl` | Updates AgentCard PnL display |
| `agent_status` | `agent_id`, `status` | Updates agent status in cards |
| `agent_registered` | `agent_id`, `name`, `persona` | Adds new agent to list |

### 3.3 Empty State

When no agents are running, the Arena page shows:
- Sleeping bot ASCII art (dimmed, opacity 0.15)
- "No agents deployed" heading
- CLI command: `cd agents && python -m src.main --persona aggressive`

---

## 4. Data Flow

```
Backend API
    ├── GET /api/agents → Agent[]
    ├── GET /api/trades → Trade[]
    ├── GET /api/arena/sessions → Session[]
    └── GET /api/leaderboard/:id → Score[]

WebSocket /ws/trades
    ├── trade → TradeFeed
    ├── pnl_update → AgentCard PnL
    ├── agent_status → AgentCard status
    └── agent_registered → Agent list
```

---

## 5. Testing

1. Start backend: `cd api && uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to `/arena`
4. Verify empty state with ASCII art and CLI command
5. Start agent: `cd agents && python -m src.main --persona aggressive`
6. Verify:
   - Agent appears in "Competing Agents" with live indicator
   - Persona badge shows correctly
   - PnL updates when trades execute
   - ArenaRing renders bars (after fetching leaderboard)
   - TradeFeed shows trades in real-time

---

## 6. Files

| File | Description |
|---|---|
| `frontend/src/pages/Arena.tsx` | Arena page with agents, ArenaRing, TradeFeed |
| `frontend/src/components/AgentCard.tsx` | Agent card with persona, status, PnL |
| `frontend/src/components/ArenaRing.tsx` | Framer-motion animated bar chart race |
| `frontend/src/components/TradeFeed.tsx` | Sidebar trade feed |
