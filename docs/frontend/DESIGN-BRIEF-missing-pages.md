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

## PAGE 3: Dashboard — Empty State (No Agent Deployed)

This is a complete variant of `tradinghunter-sandbox-dashboard.html`. The app shell (topbar, ticker, mobile tabs, terminal) stays the same. Only the main content area changes.

### Layout (same app shell, different main content)
```
┌──────────────────────────────────────────────────────────┐
│ TOPBAR (48px) — logo, nav, "NO AGENTS" indicator        │
├──────────────────────────────────────────────────────────┤
│ TICKER (32px) — scrolling prices (still live)           │
├──────────────────────────────────────────────────────────┤
│ MOBILE TABS (hidden on desktop)                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─ LEFT PANEL (280px) ─┐  ┌─ CENTER AREA ───────────┐  │
│  │ agent_config          │  │                          │  │
│  │                       │  │   (empty chart area)     │  │
│  │ [Select agent dropdown │  │                          │  │
│  │  with "No agents       │  │   ┌─────────────────┐   │  │
│  │  configured" option]  │  │   │  sleeping bot    │   │  │
│  │                       │  │   │  ASCII art       │   │  │
│  │ strategy buttons       │  │   │  (large, dim)   │   │  │
│  │ [all disabled/50%]    │  │   │                  │   │  │
│  │                       │  │   │  Deploy your     │   │  │
│  │ parameters sliders     │  │   │  first agent     │   │  │
│  │ [default values]      │  │   │                  │   │  │
│  │                       │  │   │  Configure your  │   │  │
│  │ risk inputs            │  │   │  strategy and    │   │  │
│  │ [default values]      │  │   │  enter the arena │   │  │
│  │                       │  │   │                  │   │  │
│  │ toggles [all off]     │  │   │  [▶ deploy]      │   │  │
│  │                       │  │   └─────────────────┘   │  │
│  │ [▶ deploy agent]      │  │                          │  │
│  │  button (green)       │  │                          │  │
│  └───────────────────────┘  └──────────────────────────┘  │
│                                                          │
│  ┌─ RIGHT PANEL (300px) ──────────────────────────────┐  │
│  │                                                      │  │
│  │  unrealized P&L                                      │  │
│  │  —                                                   │  │
│  │  No active positions                                 │  │
│  │                                                      │  │
│  │  ┌─ empty sparkline (flat line at 0) ────────────┐  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                      │  │
│  │  open positions                         0            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  No open positions                             │  │  │
│  │  │  Deploy an agent to start trading              │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                      │  │
│  │  recent signals                         0            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Waiting for agent signals...                  │  │  │
│  │  │                                                │  │  │
│  │  │  (terminal-like prompt)                        │  │  │
│  │  │  $ _                                           │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ TERMINAL (180px) — init messages only, idle prompt       │
└──────────────────────────────────────────────────────────┘
```

### Topbar Changes
- **Status area** (right side):
  - LIVE indicator: replaced with gray dot + `--green-dim` text "IDLE"
  - Agent ID: hidden (no agent deployed)
- Everything else unchanged

### Left Panel — Agent Config
- **Agent Select dropdown**: Shows single disabled option "No agents configured" in `--green-dim`, grayed out
- **Strategy buttons**: All 4 visible (momentum, mean_rev, breakout, custom) but at 50% opacity, not clickable. "momentum" shows as default selected.
- **Parameter sliders**: Visible but at 50% opacity. Default positions (EMA 9, RSI 14, ATR 1.5). Labels and values still readable.
- **Risk inputs**: Visible at 50% opacity. Default values shown (Max DD 8%, Position Size 2.5%, Stop Loss 3.2%, Take Profit 6.8%).
- **Execution toggles**: All 3 visible in OFF state, 50% opacity.
- **Deploy button**: FULL opacity green (`--green-terminal` background). Text: "▶ deploy agent". This is the primary CTA — it's the one interactive element on the page.

### Center — Empty Chart Area
- **Background**: `#080808` (same as normal chart)
- **Layout**: flex column, centered both axes
- **ASCII art** (centered, above text):
  ```
  Use `--green-dim` color, opacity 0.15, `--font-mono`, font-size 11px, line-height 1.1
  The art should be a large sleeping/idle robot/bot:
  
        ┌──────────────────────┐
        │  ████          ████  │
        │  ████          ████  │
        │  ██████████████████  │
        │  ██████████████████  │      ← big empty eye sockets
        │  ██    ██████    ██  │
        │  ██  Z ██████ z  ██  │      ← sleeping Z's
        │  ██    ██████    ██  │
        │  ██████████████████  │
        │  ██████████████████  │
        │  ██  ██████████  ██  │
        │  ██  ██████████  ██  │
        │  ██              ██  │
        │  ────────────────    │      ← flat line (flatline = idle)
        └──────────────────────┘
  ```
- **Heading**: `--font-display`, `clamp(28px, 4vw, 40px)`, `--surface` color, margin-bottom 12px
  - Text: "Deploy your first agent"
- **Subtext**: `--font-body`, 14px, `#888` color, max-width 400px, text-align center, line-height 1.6, margin-bottom 32px
  - Text: "Configure your strategy parameters, set risk limits, and enter the sandbox arena. No real money — just algorithms competing for alpha."
- **CTA Button**: matches `.deploy-btn` style from dashboard:
  - Background: `--green-terminal` (`#33ff33`)
  - Text color: `--fg-dark` (`#0f0f0f`)
  - Text: "▶ deploy agent"
  - Font: `--font-mono`, 13px, uppercase, letter-spacing 0.12em, bold
  - Padding: 14px 28px
  - Border: none, no border-radius
  - Hover state: `box-shadow: 0 0 20px rgba(51,255,51,0.3)`
  - Not disabled — this is the primary action

### Right Panel — Empty Stats
- **PnL Section**:
  - Label: "unrealized P&L" (same as normal), `--green-dim`, 9px uppercase
  - Value: "—" (em dash), `--font-display`, 32px, `--green-dim` (not green, not red — neutral dim)
  - Sub-text: "No active positions", 11px, `--green-dim`
  - Sparkline: flat horizontal line at center, `--green-dim` color, opacity 0.3
- **Positions Section**:
  - Header: "open positions" label + count "0"
  - Content: centered empty state inside a bordered area
    - Text 1: "No open positions", 12px, `--green-dim`
    - Text 2: "Deploy an agent to start trading", 10px, `#555`
  - No column headers shown (since there are no positions)
- **Signals Section**:
  - Header: "recent signals" label + count "0"
  - Content: centered empty state
    - Terminal-prompt style: "$ _", `--font-mono`, 14px, `--green-dim`
    - Below: "Waiting for agent signals...", 11px, `#555`

### Terminal
- Same structure as normal (titlebar with dots, output area, input line)
- **Initial messages only** (no trade output, no live updates):
  ```
  TradingHunter v0.4.1 — AI Agent Trading Sandbox
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ System initialized
  ✓ Arena #47 connected
  ⚠ No agents deployed
    Paper trading: ON | Capital: 10,000 USDT
    Configure an agent and click "deploy" to start
    Type "help" for available commands
  $ _
  ```
- Input line active (user can type commands even without agent)
- Colors: same terminal color scheme (prompt=green, success=green, warn=amber, dim=dim green)

### Mobile Tabs
- Same 4 tabs visible: 📊 chart, ⚙️ config, 📈 positions, 📡 signals
- Chart tab shows the empty CTA (centered, with ASCII art)
- Config tab shows the left panel (with deploy button active)
- Positions tab shows the right panel positions section
- Signals tab shows the right panel signals section

---

## PAGE 4: Dashboard — Loading Skeleton

Complete variant for initial data fetch. App shell stays, all content areas show pulsing placeholders.

### Layout (same app shell)
```
┌──────────────────────────────────────────────┐
│ TOPBAR — logo, nav, muted status             │
├──────────────────────────────────────────────┤
│ TICKER — scrolling (still runs if data avail)│
├──────────────────────────────────────────────┤
│ MOBILE TABS                                   │
├──────────────────────────────────────────────┤
│                                               │
│  ┌─ LEFT (280px) ─┐  ┌─ CENTER ──────────┐  │
│  │ ██████████████  │  │                    │  │
│  │ ██████████      │  │  ████████████████  │  │
│  │ ██████████████  │  │  ████████████████  │  │
│  │ ██████████      │  │  ████████████████  │  │
│  │ ██████████████  │  │  ████████████████  │  │
│  │ ██████████      │  │  ████████████████  │  │
│  │ ██████████████  │  │  ████████████████  │  │
│  │ ██████████      │  │  ████████████████  │  │
│  │ ██████████████  │  │  ████████████████  │  │
│  └─────────────────┘  │  ████████████████  │  │
│                       └────────────────────┘  │
│  ┌─ RIGHT (300px) ───────────────────────┐  │
│  │          ████████████████              │  │
│  │          ████████████                  │  │
│  │          ██████████████████████        │  │
│  │                                        │  │
│  │  ██████████████████████████████        │  │
│  │  ██████████████████████████████        │  │
│  │  ██████████████████████████████        │  │
│  │                                        │  │
│  │  ██████████████████████████████        │  │
│  │  ██████████████████████████████        │  │
│  │  ██████████████████████████████        │  │
│  │  ██████████████████████████████        │  │
│  │  ██████████████████████████████        │  │
│  └────────────────────────────────────────┘  │
│                                               │
├──────────────────────────────────────────────┤
│ TERMINAL — skeleton text lines               │
└──────────────────────────────────────────────┘
```
(█ = pulsing skeleton placeholder rectangles)

### Skeleton Animation
All skeleton elements share this animation:
- **Base color**: `--bg-panel` (`#111111`)
- **Shimmer**: lighter green tint `rgba(51,255,51,0.03)` to `rgba(51,255,51,0.06)` pulsing
- **Animation**: `pulse` keyframe, 1.5s ease-in-out infinite
  ```css
  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
  }
  ```
- **Border-radius**: 0 (match design — sharp rectangles, no rounding)
- **Border**: none on skeletons (just background-color blocks)

### Topbar
- **Status area**: Gray dot (not green, not red) + "LOADING..." text in `--green-dim`, 10px. Dots animate (first dot fades 0s, second 0.3s, third 0.6s — classic loading ellipsis).
- Everything else unchanged

### Left Panel Skeletons
Each skeleton replaces a real config element. Widths and heights should roughly match:

1. **Panel header**: `████████████` (80px × 12px)
2. **Agent select dropdown**: Tall rectangle `████████████████████████████` (full width × 36px)
3. **Strategy section title**: `██████████` (60px × 10px)
4. **Strategy buttons**: 2×2 grid of rectangles, each 50% width × 36px
5. **Parameters section title**: `██████████` (60px × 10px)
6. **3 sliders**: Each — label rectangle (80px × 10px) + wide track rectangle (full width × 24px)
7. **Risk section title**: `██████████` (70px × 10px)
8. **4 input rows**: Each — label rectangle (70px × 10px) + input rectangle (64px × 28px) right-aligned
9. **Execution section title**: `██████████` (60px × 10px)
10. **3 toggle rows**: Each — label rectangle (80px × 10px) + toggle-sized rectangle (40px × 24px) right-aligned
11. **Deploy button area**: Full-width rectangle (full width × 48px), slightly brighter green shimmer

### Center — Chart Skeleton
- **Background**: `#080808` (same as real chart)
- **Chart toolbar skeleton**:
  - Left: price label skeleton `████████████` (120px × 18px) + change badge skeleton `██████` (60px × 18px)
  - Right: 6 timeframe button skeletons, each `████` (32px × 24px)
- **Chart area skeleton**:
  - Background: `#080808`
  - 4-5 horizontal grid line skeletons: thin rectangles across width, spaced evenly, `rgba(26,58,26,0.15)`
  - 2-3 candlestick bars as tall thin rectangles: green tint `rgba(51,255,51,0.08)` and red tint `rgba(196,69,69,0.08)` alternating, heights vary (60%–90% of chart height), width ~6px, spaced across
  - EMA line: thin rectangle across width at ~65% height, `rgba(162,203,139,0.1)`, 1px tall
  - Y-axis labels: left side, 5 small rectangles (`████` = 36px × 8px), spaced evenly vertically
- **Chart overlay skeleton** (top-left):
  - 4 rows: each `██████████████` (100px × 10px), stacked with 18px gap

### Right Panel Skeletons
- **PnL Section**:
  - Label: `██████████` (80px × 9px), centered
  - Value: `████████████████` (140px × 32px), centered
  - Sub-text: `████████████` (100px × 11px), centered
  - Sparkline: narrow rectangle full width × 36px, `rgba(51,255,51,0.05)`
- **Positions Section**:
  - Header: `████████████` (80px × 9px) left + `██` (20px × 10px) right
  - Column headers: 3 rectangles in a row `██████ ██████ ██████` (each ~60px × 8px)
  - 3 data rows: each 3 rectangles in a row, slightly different widths, `--bg-panel`, 10px height
- **Signals Section**:
  - Header: `██████████` (70px × 9px) left + `██` (20px × 10px) right
  - 5 signal item skeletons: each a row with dot (6px × 6px) + time (32px × 9px) + text (120px × 9px) + badge (40px × 16px), spaced 12px apart

### Terminal Skeleton
- **Titlebar**: 3 dots (visible, static, not skeleton) + tab label skeleton `██████████` (60px × 10px)
- **Output area**: 8-10 text line skeletons:
  - Each: `████████████████████████████████████` (full width × 10px), varying lengths (60%-90% width)
  - Stacked with 12px gap
  - First one slightly greener (simulates prompt line)
- **Input line**: `>` prompt (real, not skeleton, `--green-terminal`) + input skeleton `████████████████████████` (200px × 10px)

### Mobile Tabs
- Same 4 tabs, all visible
- Each tab shows its corresponding skeleton content

---

## PAGE 5: Dashboard — Connection Lost / Error

Complete variant when WebSocket or data feed disconnects. App shell darkens slightly, warning overlay appears.

### Layout
```
┌──────────────────────────────────────────────┐
│ TOPBAR — LIVE → DISCONNECTED (red)           │
├──────────────────────────────────────────────┤
│ TICKER — frozen (last known prices, dimmed)  │
├──────────────────────────────────────────────┤
│ MOBILE TABS (still functional)               │
├──────────────────────────────────────────────┤
│                                               │
│  ┌────────────────────────────────────────────┐
│  │                                            │
│  │  ⚠                                         │
│  │  Connection lost                            │
│  │  The data feed has been interrupted.        │
│  │  Your agent is still running but we can't   │
│  │  display live updates right now.            │
│  │                                            │
│  │  Last update: 14:32:05 UTC                  │
│  │  Reconnecting in 3...                       │
│  │                                            │
│  │  [⟳ Reconnect now]                         │
│  │                                            │
│  └────────────────────────────────────────────┘
│                                               │
│  (Center chart, left panel, right panel       │
│   still visible behind overlay at 30% opacity)│
│                                               │
├──────────────────────────────────────────────┤
│ TERMINAL — last messages frozen + warning     │
└──────────────────────────────────────────────┘
```

### Topbar Changes
- **Status area** (right side):
  - LIVE indicator dot: changes from green to RED (`--red`), blinking faster (0.5s instead of 1s)
  - Text: "DISCONNECTED" in `--red-light`, uppercase, 10px, letter-spacing 0.1em
  - Agent ID: still shown (agent is still running), but dimmed (50% opacity)
- **Everything else**: unchanged

### Ticker
- **Prices frozen** at last known values
- **Animation stopped** (no scrolling)
- **Dimmed**: opacity 0.4
- Small red indicator added at left edge: "● OFFLINE" in `--red-light`, 8px uppercase

### Main Overlay
- **Position**: absolute, covers entire main content area (inset 0)
- **Background**: `rgba(10,10,10,0.85)` — dark semi-transparent overlay
- **Z-index**: above panels, below mobile tabs
- **Content**: centered flex column, text-align center

### Overlay Content
1. **Warning icon** (top, large):
   - `⚠` character, 48px, `--amber` color, margin-bottom 20px
   - Subtle pulse animation (opacity 0.6→1, 2s infinite)

2. **Heading**: `--font-display`, `clamp(24px, 3vw, 32px)`, `--amber` color, margin-bottom 12px
   - Text: "Connection lost"

3. **Description**: `--font-body`, 13px, `#888`, max-width 420px, line-height 1.6, margin-bottom 8px
   - Text: "The data feed has been interrupted. Your agent is still running but we can't display live updates right now."

4. **Last update timestamp**: `--font-body`, 11px, `--green-dim`, margin-bottom 28px
   - Format: "Last update: 14:32:05 UTC"
   - The timestamp should be from a real variable (frozen at disconnect time)

5. **Countdown text**: `--font-body`, 12px, `--amber`, margin-bottom 20px
   - Text: "Reconnecting in 3..." (counts down: 3, 2, 1, then "Reconnecting...")
   - The number animates (countdown)
   - After "Reconnecting..." stays for 5s, then loops back to "Reconnecting in 3..."

6. **Retry button**:
   - Background: transparent
   - Border: 2px solid `--amber`
   - Text color: `--amber`
   - Text: "⟳ Reconnect now"
   - Font: `--font-mono`, 12px, uppercase, letter-spacing 0.08em
   - Padding: 12px 28px
   - Hover: border color → `--amber` brighter, `box-shadow: 0 0 16px rgba(212,160,23,0.3)`
   - Cursor: pointer

### Panels Behind Overlay
All three panels (left config, center chart, right stats) remain visible but:
- **Opacity**: 0.3
- **Pointer events**: none (can't interact)
- **Last known data** frozen in place
- Chart shows last candles (dimmed, frozen — no new candles appearing)
- PnL shows last known value (dimmed, with "—" sub-text "Last known")

### Terminal
- **Titlebar**: dots unchanged. Tab label dimmed.
- **Output**: Last messages still visible, frozen, opacity 0.5
- **New warning line** (top of output, amber):
  ```
  ⚠ WebSocket disconnected at 14:32:05 UTC
  ⚠ Attempting to reconnect...
  ```
- **Input line**: `>` prompt grayed out, placeholder text: "reconnecting..." in `--amber`, input disabled
- **Every 3 seconds**: new amber line appears:
  ```
  ⚠ Reconnection attempt 1... failed (will retry in 3s)
  ⚠ Reconnection attempt 2... failed (will retry in 3s)
  ⚠ Reconnection attempt 3... failed (will retry in 3s)
  ```

### Recovery State (when reconnection succeeds)
This transition state lasts ~2 seconds before reverting to normal dashboard:
1. Overlay fades out (opacity 0.85 → 0, transition 0.5s)
2. Topbar: red dot → green dot, "DISCONNECTED" → "LIVE"
3. Ticker: undimmed, animation resumes
4. Terminal: new green line "✓ Reconnected at 14:35:12 UTC"
5. All panels: opacity 0.3 → 1.0
6. Data refreshes with latest values

### Mobile Tabs
- All 4 tabs still functional (can switch between frozen panels)
- But each panel shows 30% opacity frozen content
- Overlay visible on all tab views

---

## Additional State: Error Banner (Non-blocking)

A less severe variant — a banner at the top of the main area for transient errors that don't require full overlay.

### Banner Design
- **Position**: below topbar + ticker, above main content
- **Height**: 36px
- **Background**: `rgba(196,69,69,0.1)` (very subtle red)
- **Border-bottom**: 1.5px solid `--red`
- **Layout**: flex row, items centered, justify-content space-between, padding 0 16px

### Banner Content
1. **Left**: `⚠` icon 12px + message in `--red-light`, 11px
   - Text varies by error type:
     - "Data feed latency: 2.3s (normal: <0.5s)"
     - "Failed to fetch positions — data may be stale"
     - "API rate limit reached — retrying in 10s"
2. **Right**: "Dismiss" button — small text `--red-light`, 9px uppercase, cursor pointer, no border

### When to use banner vs overlay
- **Banner**: transient errors (API rate limit, slow data, single endpoint failure)
- **Overlay**: hard disconnect (WebSocket closed, no data for 10+ seconds)

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

## SKELETON-SPECIFIC TOKENS
```
--skeleton-base: #111111
--skeleton-shimmer-low: rgba(51,255,51,0.03)
--skeleton-shimmer-high: rgba(51,255,51,0.06)
--overlay-bg: rgba(10,10,10,0.85)
--frozen-opacity: 0.3
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
