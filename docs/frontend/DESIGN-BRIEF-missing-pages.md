# Design Brief — Missing Pages & States

Use the same design tokens as `tradinghunter-sandbox-dashboard.html` (dark mode).
Same fonts, same scanline overlay, same border conventions, same terminal aesthetic.

---

## PAGE 1: Agent Profile (`/agents/:id`)

### Layout
Dark app shell matching the dashboard:
```
┌──────────────────────────────────────────────┐
│ TOPBAR (48px) — logo, nav, LIVE indicator    │
├──────────────────────────────────────────────┤
│ TICKER (32px) — scrolling prices             │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─ Agent Header ─────────────────────────┐  │
│  │ persona badge · status · ERC-8004 info │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌── Stat Cards (4 across) ───────────────┐  │
│  │ Total PnL │ Sharpe │ Win Rate │ Trades  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌─ PnL Equity Curve (recharts) ──────────┐  │
│  │ full-width chart, dark bg              │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌─ Strategy Config ─┬─ Reputation ───────┐  │
│  │ indicators, params │ feedback tags      │  │
│  └────────────────────┴───────────────────┘  │
│                                              │
│  ┌─ Trade History Table ──────────────────┐  │
│  │ time │ pair │ side │ price │ size │ pnl │  │
│  └────────────────────────────────────────┘  │
│                                              │
└──────────────────────────────────────────────┘
```

### Section 1: Agent Header
- **Layout**: flex row, items centered, gap 16px, padding 24px 32px
- **Left**: Agent avatar placeholder (48×48px square, dark bordered box with first 2 chars of agent ID in green-terminal)
- **Center**:
  - Agent name: `--font-display`, 28px, `--surface` color (e.g. "Momentum Hunter #0047")
  - Persona badge: inline bordered tag, `--green-terminal` border + text, 10px uppercase (e.g. "AGGRESSIVE")
  - Status indicator: green blinking dot + "LIVE" or red dot + "STOPPED", 10px
  - ERC-8004 info: "Token ID: 47 · Registered: 2025-05-15" in `--green-dim`, 10px
- **Right**: Action buttons:
  - "View on Explorer" — secondary button style, links to Mantle explorer
  - "Back to Arena" — secondary button style

### Section 2: Performance Stat Cards
- **Layout**: 4-column grid, gap 16px, padding 0 32px 24px
- **Each card**:
  - Background `--bg-panel`, border 1.5px solid `--border-dark`
  - Padding: 20px 16px
  - Label: 9px uppercase, `--green-dim`, letter-spacing 0.12em, margin-bottom 8px
  - Value: `--font-display`, `clamp(32px, 4vw, 48px)`, `--accent` for neutral, `--green-terminal` for positive, `--red-light` for negative
  - Sub-text: 10px, `--green-dim`, shows % or comparison
  - Hover: slight background lighten
- **Cards needed**:
  1. Total PnL — green if positive, red if negative, shows % of starting capital
  2. Sharpe Ratio — neutral (accent color), shows interpretation text ("Excellent", "Good", etc.)
  3. Win Rate — neutral, shows win/loss count below
  4. Total Trades — neutral, shows avg hold time below

### Section 3: PnL Equity Curve
- **Container**: full-width, padding 0 32px, margin-bottom 24px
- **Chart area background**: `#080808`, border 1.5px solid `--border-dark`, height 320px
- **Chart toolbar** (above chart):
  - Left: "Equity Curve" label, `--font-display` 18px
  - Right: timeframe selector buttons (1D, 1W, 1M, 3M, ALL) — same style as dashboard timeframe buttons
- **Chart** (recharts LineChart):
  - Grid: `rgba(26,58,26,0.3)` horizontal lines
  - Line: `#33ff33` for values above starting capital, `#C44545` for below
  - Area fill: gradient from line color to transparent, opacity 0.08
  - X-axis: dates, `--green-dim`, 10px monospace
  - Y-axis: USDT values, `--green-dim`, 10px monospace
  - Reference line at starting capital (dashed, `rgba(26,58,26,0.5)`)
  - Tooltip: dark bg, white border, monospace values, timestamp + value

### Section 4: Two-Column Footer
Left col (60% width):
- **Strategy Configuration**:
  - Section title: "strategy_config" — same panel-header style (10px uppercase, `--green-dim`, `> ` prefix)
  - Strategy name: `--font-display`, 20px, `--green-light`
  - Parameter table: 2-column grid
    - Left: param name (green-terminal, monospace, 11px)
    - Right: value (amber, monospace, 11px)
  - Examples: "EMA Fast: 9", "EMA Slow: 21", "RSI Period: 14", "ATR Multiplier: 1.5x"
  - Risk params below: "Max Drawdown: 8%", "Position Size: 2.5%", "Stop Loss: 3.2%", "Take Profit: 6.8%"

Right col (40% width):
- **Reputation Tags**:
  - Section title: "reputation" — same style
  - Tags as bordered boxes (like signal-type badges):
    - Each tag: padding 6px 12px, border 1px solid, monospace 10px, uppercase
    - Colors: PNL → `--green-terminal`, CONSISTENCY → `--amber`, SHARPE → `--green-light`, WINRATE → `--green-terminal`
    - Score shown next to each: (e.g. "PNL 8.5", "CONSISTENCY 7.2")
  - Aggregated score at top: font-display 36px, accent color
  - "Submit Feedback" button at bottom (only if wallet connected)

### Section 5: Trade History Table
- **Container**: padding 0 32px
- **Section title**: "trade_history" — panel-header style
- **Table**:
  - Header row: dark bg, uppercase, 10px, `--green-terminal`
  - Columns: Time | Pair | Side | Price | Size | PnL
  - Rows: border-bottom 1px solid `rgba(26,58,26,0.5)`, hover bg `rgba(51,255,51,0.02)`
  - Time: monospace, 11px, `--green-dim`, format "14:32:05"
  - Pair: monospace, 11px, `--surface` (e.g. "BTC/USD")
  - Side: "LONG" in green (`--green-terminal`) or "SHORT" in red (`--red-light`), 10px uppercase bordered tag
  - Price: monospace, 11px, tabular-nums, `--surface`
  - Size: monospace, 11px, tabular-nums, `#aaa`
  - PnL: monospace, 12px, tabular-nums, green or red
- **Pagination**: bottom of table
  - "← Previous" / "Next →" buttons, secondary button style
  - Page indicator: "Page 1 of 5" in `--green-dim`, monospace

### States for Agent Profile
1. **Loading**: Skeleton cards (dark pulsing rectangles), chart area shows loading overlay
2. **Agent Not Found**: centered error with "Agent not found" in `--red-light`, "Back to Arena" button
3. **No Trades Yet**: empty table with "No trades executed yet" in `--green-dim`, centered
4. **Wallet Disconnected**: reputation section shows "Connect wallet to submit feedback" CTA

---

## PAGE 2: Leaderboard (`/leaderboard`)

### Layout
```
┌──────────────────────────────────────────────┐
│ TOPBAR (48px)                                │
├──────────────────────────────────────────────┤
│ TICKER (32px)                                │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─ Session Selector ─────────────────────┐  │
│  │ [Arena #47 ▼]  ·  Status: LIVE  ·  3 agents │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌─ Top 3 Podium ─────────────────────────┐  │
│  │     🥈         🥇          🥉           │  │
│  │  Agent #31   Agent #47   Agent #92     │  │
│  │  +8.2%       +12.4%      +5.7%        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌─ Rankings Table ───────────────────────┐  │
│  │ # │ Agent │ PnL │ Sharpe │ Win% │ Trd  │  │
│  │ 1 │ #0047 │ +12.4% │ 1.84 │ 64% │ 142 │  │
│  │ 2 │ #0031 │ +8.2%  │ 1.51 │ 58% │ 98  │  │
│  │ 3 │ #0092 │ +5.7%  │ 1.32 │ 61% │ 76  │  │
│  │ 4 │ ...   │ ...   │ ...   │ ... │ ... │  │
│  └────────────────────────────────────────┘  │
│                                              │
└──────────────────────────────────────────────┘
```

### Section 1: Session Selector
- **Layout**: flex row, padding 16px 32px, border-bottom 1.5px solid `--border-dark`
- **Left**: `<select>` dropdown for arena session:
  - Dark bg (`--fg-dark`), green-light text, border 1.5px solid `--border-dark`
  - Options: "Arena #47 — May 2025", "Arena #46 — April 2025", etc.
- **Center**: Session info:
  - Status dot (green blinking if live, gray if ended)
  - "LIVE" or "ENDED" text, 10px uppercase
  - Agent count: "3 agents competing"
- **Right**: Session dates: "May 15 — May 22, 2025" in `--green-dim`

### Section 2: Top 3 Podium
- **Layout**: flex row, justify-content center, gap 32px, padding 40px 32px
- **Cards** (3 across, gold/silver/bronze order):
  - **1st place** (center, slightly larger):
    - Width: 220px, border-color: `--amber` (gold)
    - Rank: large medal emoji 🥇 48px
    - Agent name: `--font-display`, 22px, `--surface`
    - Agent ID: monospace, 12px, `--green-dim`
    - PnL: `--font-display`, 36px, `--green-terminal`
    - Sub-stat row: "Sharpe 1.84 · Win 64% · 142 trades", 10px, `--green-dim`
  - **2nd place** (left, slightly smaller):
    - Width: 200px, border-color: `--green-dim` (silver-ish)
    - 🥈, 40px
    - Same structure, scaled down slightly
  - **3rd place** (right, slightly smaller):
    - Width: 200px, border-color: `--accent` (bronze)
    - 🥉, 40px
    - Same structure, scaled down slightly
- **Card common**: background `--bg-panel`, border 2px solid, padding 24px 20px, text-align center

### Section 3: Rankings Table
- **Container**: padding 0 32px 40px
- **Table header**: "rankings" — panel-header style
- **Sort controls**: clickable column headers with sort arrow indicator
  - Active sort column: `--green-terminal` color
  - Arrow: ▲ for asc, ▼ for desc
- **Columns**: Rank | Agent | PnL | Sharpe | Win Rate | Trades
  - Rank: 4 (no medal), monospace 12px
  - Agent: linked name (clickable to profile), monospace 12px
  - PnL: color-coded, tabular-nums
  - Sharpe: tabular-nums, 1 decimal
  - Win Rate: percentage, tabular-nums
  - Trades: number
- **Row hover**: `background: rgba(51,255,51,0.02)`
- **Highlight top 3 rows** with subtle left border accent (gold/silver/bronze)
- **Current user's agent** (if wallet connected): bg `rgba(51,255,51,0.04)`, subtle border

### States for Leaderboard
1. **Loading**: skeleton rows (6 rows of pulsing rectangles)
2. **No sessions**: centered "No arena sessions yet" with CTA to create one
3. **Session with no agents**: "No agents competed in this session" empty state
4. **Error**: "Failed to load leaderboard" with retry button

---

## STATE VARIANT: Dashboard — Empty States

These are variants of `tradinghunter-sandbox-dashboard.html`:

### Variant A: No Agent Deployed
- **Center chart**: replaced with centered CTA
  - Large `--font-display` text: "Deploy your first agent"
  - Subtext: "Configure your strategy and enter the arena"
  - Green "▶ deploy agent" button (matches existing deploy button style)
  - ASCII art of sleeping robot in background (opacity 0.05)
- **Right panel PnL**: shows "—" with "No positions" label
- **Terminal**: shows only init lines, no trade output

### Variant B: Loading Skeleton
- **Chart area**: dark bg with subtle pulsing placeholder bars
- **PnL**: pulsing `--bg-panel` rectangle (width 120px × 32px)
- **Positions**: 3 skeleton rows (pulsing rectangles)
- **Signals**: 5 skeleton rows
- **Terminal**: skeleton text lines

### Variant C: Connection Lost
- **Topbar**: LIVE indicator turns red, text changes to "DISCONNECTED"
- **Chart overlay**: centered warning "Connection lost — reconnecting..." with amber text
- **Terminal**: yellow warning line "⚠ WebSocket disconnected"

---

## COLOR REFERENCE (copy-paste into your design tool)

Dark mode tokens (same as dashboard):
```
--bg-dark: #0a0a0a
--surface: oklch(100% 0 0)
--fg-dark: #0f0f0f
--bg-panel: #111111
--border-dark: #1a3a1a
--green-terminal: #33ff33
--green-dim: #1a8a1a
--green-light: #A2CB8B
--red: #C44545
--red-light: #e86565
--amber: #d4a017
--accent: oklch(60% 0.22 25)
--font-display: 'Times New Roman', 'Iowan Old Style', Georgia, serif
--font-body: ui-monospace, 'IBM Plex Mono', 'JetBrains Mono', Menlo, monospace
```

## TYPOGRAPHY REMINDER
- Headlines/stat numbers: `--font-display` (serif), normal weight, tight line-height
- Everything else: `--font-body` (monospace), 10-14px range
- Labels: 9-10px uppercase, letter-spacing 0.1em-0.18em, `--green-dim`
- Terminal: 11px monospace, line-height 1.7

## GLOBAL EFFECTS (apply to every page)
1. Scanline overlay (`body::after`)
2. `::selection` accent color
3. No border-radius anywhere
4. All borders 1.5-2px solid
