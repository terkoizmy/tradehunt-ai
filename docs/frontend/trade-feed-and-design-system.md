# TradeFeed, Contract Events & Quant Terminal Design System

> Issue #10 implementation — real-time trade feed sidebar, on-chain event listeners, and the global quant terminal design system.

---

## 1. Design System — "Quant Terminal"

### 1.1 Philosophy

The TradingHunter UI follows a **dark quant terminal** aesthetic inspired by old-school Bloomberg terminals and hacker culture:
- Dark background with neon green accents
- Sharp edges everywhere — no border-radius
- Monospace fonts for data, serif fonts for display numbers
- Subtle scanline overlay for CRT-like texture

### 1.2 Color Tokens

| Token | Value | Usage |
|---|---|---|
| `--bg-dark` | `#0a0a0a` | App body background |
| `--fg-dark` | `#0f0f0f` | Topbar, terminal, panels |
| `--bg-panel` | `#111111` | Cards, sidebars, tables |
| `--border-dark` | `#1a3a1a` | Borders, dividers |
| `--green-terminal` | `#33ff33` | Neon green — profits, success, buy |
| `--green-dim` | `#1a8a1a` | Muted green — labels, secondary text |
| `--green-light` | `#A2CB8B` | Light green — nav links, body text |
| `--red` | `#C44545` | Losses, sell signals, errors |
| `--red-light` | `#e86565` | Lighter red — error text |
| `--amber` | `#d4a017` | Warnings, highlights |
| `--accent` | `oklch(60% 0.22 25)` | CTAs, warm red-orange highlights |
| `--surface` | `oklch(100% 0 0)` | White — primary text on dark |

### 1.3 Typography

```css
--font-display: 'Times New Roman', 'Iowan Old Style', Georgia, serif;
--font-body: ui-monospace, 'IBM Plex Mono', 'JetBrains Mono', Menlo, monospace;
--font-mono: ui-monospace, 'IBM Plex Mono', 'JetBrains Mono', Menlo, monospace;
```

| Element | Font | Size | Notes |
|---|---|---|---|
| Display / stat numbers | `--font-display` | `clamp(32px, 4vw, 48px)` | Normal weight, tight line-height |
| Body / UI | `--font-body` | 12–14px | 1.5 line-height |
| Labels / eyebrows | `--font-body` | 9–10px | uppercase, `letter-spacing: 0.1em–0.18em`, `--green-dim` |
| Terminal / code | `--font-mono` | 10–13px | 1.7 line-height |

### 1.4 Global Effects

**Scanline overlay** — applied to `body::after`:
```css
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0,0,0,0.015) 2px, rgba(0,0,0,0.015) 4px
  );
  pointer-events: none;
  z-index: 9999;
}
```

**Selection color**:
```css
::selection { background: var(--accent); color: var(--surface); }
```

### 1.5 Border & Spacing Conventions

- **Borders**: Always `1.5px–2px solid var(--border-dark)`. Never rounded.
- **Section dividers**: `border-bottom: 2px solid var(--border-dark)`
- **Panel gutters**: 14–20px padding
- **No border-radius anywhere** on TradingHunter components

---

## 2. TradeFeed Component

### 2.1 Location

`frontend/src/components/TradeFeed.tsx`

### 2.2 Props

```typescript
interface Props {
  trades: Trade[];      // From WebSocket or REST API
  connected?: boolean;  // WebSocket connection status
}
```

### 2.3 Visual Design

The TradeFeed is a sidebar panel matching the dashboard's "signals" section:

```
┌─ trade_feed ───────────── LIVE ─────┐
│                                     │
│ ● 14:32:05  BTC/USD  [BUY]  +12.47 │
│   @67,842.30 · Qty: 0.1500          │
│   "RSI divergence confirmed..."     │
│ ─────────────────────────────────── │
│ ● 14:31:22  ETH/USD [SELL]   -5.23 │
│   @3,421.10 · Qty: 2.5000           │
│   "Stop loss triggered"             │
│                                     │
└─────────────────────────────────────┘
```

Each trade item (`tf-item`) contains:
- **Dot** (`tf-dot`): green for buy, red for sell
- **Time** (`tf-time`): `HH:MM:SS` in `--green-dim`
- **Symbol** (`tf-symbol`): pair name in `--surface`
- **Side badge** (`tf-badge`): `BUY` (green border/text) or `SELL` (red border/text)
- **PnL** (`tf-pnl`): right-aligned, green for positive, red for negative
- **Details** (`tf-detail`): price and quantity in `--green-dim`
- **Reasoning** (`tf-reasoning`): italic snippet in `#888`, truncated at 60 chars

### 2.4 Behavior

- **Auto-scroll**: Newest trades appear at the top; list auto-scrolls to top on new items
- **Max 100 trades**: Only the most recent 100 are rendered
- **Empty state**: Shows terminal prompt `$ _` with "Waiting for agent signals..."
- **Connection status**: Header shows `LIVE` (green) or `OFFLINE` (dim)

### 2.5 Data Flow

```
Backend WebSocket (/ws/trades)
    ↓
useWebSocket hook → parses JSON → Trade object
    ↓
Arena page state → trades array
    ↓
TradeFeed component → renders scrolling list
```

---

## 3. Contract Event Listeners

### 3.1 Location

`frontend/src/hooks/useContractEvents.ts`

### 3.2 Hooks

#### `useTradeEvents()`

Listens to `TradeExecuted` events from the `TradeRegistry` contract via wagmi's `useWatchContractEvent`.

**Returns**: `TradeEvent[]` — array of decoded on-chain events (max 100, deduplicated by `transactionHash + logIndex`).

**Event shape**:
```typescript
interface TradeEvent {
  agentId: bigint;
  symbol: string;
  side: string;
  price: bigint;
  quantity: bigint;
  pnl: bigint;
  timestamp: bigint;
  blockNumber?: bigint;
  transactionHash?: string;
  logIndex?: number;
}
```

**ABI used**:
```solidity
event TradeExecuted(
    uint256 indexed agentId,
    string symbol,
    string side,
    uint256 price,
    uint256 quantity,
    int256 pnl,
    uint256 timestamp
);
```

**Deduplication**: Events are deduplicated by `(transactionHash, logIndex)` to prevent duplicates on reorgs or reconnects.

**Disabled state**: If `CONTRACTS.tradeRegistry` is the zero address, the hook passes `address: undefined` to `useWatchContractEvent`, which safely disables watching until a real contract address is configured.

#### `useAgentLinkedEvents()`

Listens to `AgentLinked` events (agent wallet → on-chain ID mapping).

### 3.3 Merging On-Chain + WebSocket Data

To display verified trades (both off-chain real-time and on-chain confirmed):

1. **WebSocket trades** populate the TradeFeed in real-time (fast, off-chain)
2. **On-chain events** arrive with a slight delay (block confirmation)
3. A parent component can match WebSocket trades to on-chain events via `tx_hash` on the `Trade` object
4. When matched, a verification badge can be shown on the TradeFeed item

Example merge pattern:
```typescript
const trades = useWebSocket(...);       // real-time
const chainEvents = useTradeEvents();   // on-chain confirmed

// In component: check if trade.tx_hash matches any chainEvent.transactionHash
const isVerified = (trade: Trade) =>
  chainEvents.some(e => e.transactionHash === trade.tx_hash);
```

---

## 4. WebSocket Hook

### 4.1 Location

`frontend/src/hooks/useWebSocket.ts`

### 4.2 API

```typescript
function useWebSocket<T>(url: string | null): {
  data: T | null;           // Last parsed JSON message
  connected: boolean;      // true when readyState === "open"
  readyState: "connecting" | "open" | "closed" | "error";
  error: Error | null;
}
```

### 4.3 Features

- **Auto-reconnect**: On disconnect, automatically reconnects after 3 seconds
- **JSON parsing**: Automatically parses incoming messages as JSON
- **Parse error resilience**: Invalid JSON messages are silently ignored; previous valid data is preserved
- **Cleanup**: Clears reconnect timers and closes socket on unmount

---

## 5. Global CSS

### 5.1 Location

`frontend/src/styles/global.css`

### 5.2 What Changed

**Before**: Generic dark theme with rounded corners (`border-radius: 8px`), modern sans-serif headings, standard card styling.

**After**: Full quant terminal design system:
- All tokens aligned with `tradinghunter-sandbox-dashboard.html` and `tradinghunter-agent-profiles.html`
- Sharp edges everywhere (no border-radius on `.card`, `.btn`, `.badge`, etc.)
- Scanline overlay on body
- Serif display font (`Times New Roman` / `Georgia`) for stat numbers
- Monospace body font (`JetBrains Mono`) for everything else
- Backward-compatible aliases for old CSS variables (`--bg-primary`, `--accent-green`, etc.) so existing inline styles don't break

### 5.3 Backward-Compatible Aliases

Old variable names are mapped to new tokens so existing pages (Home, Leaderboard, AgentProfile) continue to work until they are rewritten in issues #8 and #9:

| Old | Maps To |
|---|---|
| `--bg-primary` | `--bg-dark` |
| `--bg-secondary` | `--fg-dark` |
| `--bg-card` | `--bg-panel` |
| `--border` | `--border-dark` |
| `--text-primary` | `--surface` |
| `--text-muted` | `--green-dim` |
| `--accent-green` | `--green-terminal` |
| `--accent-red` | `--red-light` |
| `--font-sans` | `--font-body` |

---

## 6. Testing

### 6.1 Manual Test Steps

1. Start the backend: `cd api && uvicorn src.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to `/arena`
4. Verify TradeFeed shows empty state with `$ _` prompt
5. Start an agent: `cd agents && python -m src.main --persona aggressive`
6. Verify trades appear in TradeFeed with:
   - Correct color coding (green buy, red sell)
   - PnL values color-coded
   - Auto-scroll to newest
   - Connection status shows "LIVE"
7. Trigger a WebSocket disconnect (stop backend)
8. Verify status changes to "OFFLINE" and auto-reconnects when backend restarts

### 6.2 Contract Events

To test contract event listening:
1. Deploy TradeRegistry to Mantle Sepolia
2. Update `frontend/src/lib/contracts.ts` with deployed address
3. Link an agent wallet and emit a `TradeExecuted` event
4. Verify the event appears in browser console or via a component using `useTradeEvents()`

---

## 7. Files Modified / Created

| File | Action | Description |
|---|---|---|
| `frontend/src/styles/global.css` | **Rewrite** | Quant terminal design system tokens + global effects |
| `frontend/src/components/TradeFeed.tsx` | **Rewrite** | Sidebar trade feed with signal-item design |
| `frontend/src/hooks/useContractEvents.ts` | **Rewrite** | Proper ABI, deduplication, disabled on zero address |
| `frontend/src/hooks/useWebSocket.ts` | **Update** | Auto-reconnect, connection states, error handling |
| `frontend/src/pages/Arena.tsx` | **Update** | Pass `connected` prop to TradeFeed |
| `docs/frontend/trade-feed-and-design-system.md` | **Create** | This documentation |
