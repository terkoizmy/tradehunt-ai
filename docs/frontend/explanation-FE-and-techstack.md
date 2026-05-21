# Frontend — Architecture, Design System & Tech Stack

> **Source of truth**: The 3 HTML files in this directory (`tradinghunter-landingpage.html`, `tradinghunter-sandbox-dashboard.html`, `tradinghunter-docs.html`) define the visual contract. Every component, color, spacing, and interaction must match those exports. Do not invent new patterns — extract from the HTML.

---

## 1. Design System — "Quant Terminal"

### 1.1 Color Tokens

There are **two color modes** depending on the surface:

**Dashboard / app screens (dark mode)** — match `tradinghunter-sandbox-dashboard.html`:
| Token | Value | Usage |
|---|---|---|
| `--bg-dark` | `#0a0a0a` | App body background |
| `--fg-dark` | `#0f0f0f` | Topbar, terminal, panels |
| `--bg-panel` | `#111111` | Left sidebar, right panel |
| `--border-dark` | `#1a3a1a` | Borders everywhere |
| `--green-terminal` | `#33ff33` | Neon green — profits, success, buy signals |
| `--green-dim` | `#1a8a1a` | Muted green — labels, secondary text |
| `--green-light` | `#A2CB8B` | Light green — nav links, body text |
| `--red` | `#C44545` | Losses, sell signals, stop buttons |
| `--red-light` | `#e86565` | Lighter red — error text |
| `--amber` | `#d4a017` | Warnings |
| `--accent` | `oklch(60% 0.22 25)` | CTAs, highlights (warm red-orange) |
| `--surface` | `oklch(100% 0 0)` | White — primary text on dark |
| `--font-display` | `'Times New Roman', 'Iowan Old Style', Georgia, serif` | Headlines, stat numbers |
| `--font-body` | `ui-monospace, 'IBM Plex Mono', 'JetBrains Mono', Menlo, monospace` | Body, UI, terminal |

**Landing page (light mode)** — match `tradinghunter-landingpage.html`:
| Token | Value | Usage |
|---|---|---|
| `--bg` | `oklch(98% 0.004 240)` | Body background |
| `--surface` | `oklch(100% 0 0)` | Cards, white areas |
| `--fg` | `oklch(15% 0.02 100)` | Near-black — main text, dark sections |
| `--muted` | `oklch(40% 0.02 100)` | Secondary text |
| `--border` | `oklch(15% 0.02 100)` | Borders on light sections |
| `--accent` | `oklch(60% 0.22 25)` | Same accent as dark |
| `--green` | `#5B7E3C` | Muted olive green |
| `--green-light` | `#A2CB8B` | Light green text |
| `--green-pale` | `#E8F5BD` | Hover backgrounds |
| `--green-terminal` | `#33ff33` | Neon green (same as dark) |
| `--green-dim` | `#1a8a1a` | Dim green |
| `--red` | `#C44545` | Red for live indicators |
| `--amber` | `#d4a017` | Amber for warnings |

**CRITICAL**: Do not introduce warm beige/cream/peach/pink/orange-brown backgrounds. Stick to the palette above.

### 1.2 Typography

```
--font-display: 'Times New Roman', 'Iowan Old Style', Georgia, serif;
--font-body: ui-monospace, 'IBM Plex Mono', 'JetBrains Mono', Menlo, monospace;
--font-mono: ui-monospace, 'IBM Plex Mono', 'JetBrains Mono', Menlo, monospace;
```

**Rules**:
- **Display/headings**: `--font-display`, normal weight (400), tight line-height (0.85–1.05), large sizes via `clamp()`
- **Body/UI**: `--font-body`, 12–14px base, 1.5–1.6 line-height
- **Terminal/code**: `--font-mono`, 10–13px, 1.7–1.8 line-height
- **Labels/eyebrows**: 9–10px, uppercase, letter-spacing 0.1em–0.18em, color `--green-dim`
- **Stat numbers**: `--font-display`, large sizes (40px–64px via clamp), color `--accent`

### 1.3 Global Effects

These are applied globally — do NOT remove them:

```css
/* Scanlines overlay */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0,0,0,0.018) 2px, rgba(0,0,0,0.018) 4px
  );
  pointer-events: none;
  z-index: 9999;
}

/* Selection color */
::selection { background: var(--accent); color: var(--surface); }
```

### 1.4 Border & Spacing Conventions

- **Borders**: Always `1.5px–2px solid var(--border-dark)` or `var(--border)`. Never rounded (`border-radius: 0` everywhere).
- **Section dividers**: `border-bottom: 2px solid var(--border-dark)`
- **Panel gutters**: 14–20px padding
- **Section padding**: 48–100px on desktop, 20–32px on mobile
- **No border-radius anywhere** — the design is sharp-edged

### 1.5 Component Conventions

**Buttons**:
```css
.btn-primary {
  background: var(--accent);          /* warm red */
  color: var(--surface);
  border: 2px solid var(--accent);
  padding: 14px 32px;
  font-family: var(--font-mono);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  cursor: pointer;
  /* Hover: translateY(-2px) + box-shadow glow */
}
.btn-secondary {
  background: transparent;
  color: var(--green-light);
  border: 2px solid var(--green);
  /* Hover: border-color → var(--green-terminal) + green glow */
}
```

**Toggles** (for on/off switches):
```css
.toggle {
  width: 40px; height: 24px;
  background: var(--border-dark);
  border: 1px solid var(--green-dim);
  /* Knob: 16×16px, slides 16px right when .on */
  /* .on state: background → rgba(51,255,51,0.2) */
}
```

**Terminal dots** (appear on terminal headers):
- `.r` = red dot (`var(--red)`)
- `.y` = amber dot (`var(--amber)`)
- `.g` = green dot (`var(--green)`)
- Each: 8–10px diameter, `border-radius: 50%`, 1.5px border same color

**Labels / Eyebrows** (section labels everywhere):
```css
.sec-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--green-dim);
  display: flex;
  align-items: center;
  gap: 10px;
}
.sec-label::before {
  content: '>';
  color: var(--green-terminal);
  font-weight: 700;
}
```

**System Stamp** (used on landing page):
```css
.sys-stamp {
  font-size: 10px; text-transform: uppercase;
  letter-spacing: 0.15em; color: var(--green-dim);
  border: 1px solid var(--green-dim);
  padding: 3px 8px;
}
.sys-stamp::before { content: '>'; color: var(--green-terminal); }
```

**Blinking cursor**:
```css
.cursor-blink::after {
  content: '█';
  animation: blink-cursor 1s step-end infinite;
  color: var(--green-terminal);
}
```

**Live indicator**:
```css
.live-indicator {
  display: flex; align-items: center; gap: 6px;
  font-size: 9px; text-transform: uppercase;
  letter-spacing: 0.15em; color: var(--red);
}
.live-indicator::before {
  content: ''; width: 6px; height: 6px;
  background: var(--red);
  animation: blink-dot 1s infinite;
}
```

---

## 2. Tech Stack

| Library | Version | Purpose |
|---|---|---|
| React | 18 | UI library |
| Vite | 5 | Build tool |
| TypeScript | 5.5 | Type safety |
| React Router | v6 | Client-side routing |
| wagmi | v2 | Wallet connection + contract reads |
| viem | v2 | Low-level chain interactions |
| framer-motion | 11 | Animations (bars, page transitions, reveals) |
| recharts | 2 | Equity curves, PnL charts |

---

## 3. Page → Design Mapping

Each page in our app maps to a specific HTML reference:

| App Route | Page Component | Design Reference |
|---|---|---|
| `/` | `Home.tsx` | `tradinghunter-landingpage.html` (hero, about, features, ticker, CTA) |
| `/arena` | `Arena.tsx` | `tradinghunter-sandbox-dashboard.html` (layout, chart, terminal) |
| `/arena/:id` | `ArenaDetail.tsx` | `tradinghunter-sandbox-dashboard.html` (full dashboard) |
| `/agents/:id` | `AgentProfile.tsx` | Dark mode cards + chart (use dashboard tokens) |
| `/leaderboard` | `Leaderboard.tsx` | Dark mode table (use dashboard tokens) |

---

## 4. Page Specifications

### 4.1 Home (`/`) — Landing Page

Reference: `tradinghunter-landingpage.html` (light mode)

**Layout**: Single scrollable column, light background.

**Sections (top to bottom)**:
1. **Nav** — sticky, `height: 56px`, dark background (`rgba(15,15,15,0.95)`), backdrop blur. Logo left (`>_` prefix + "Trading" + "Hunter" in accent). Nav links: about, systems, terminal, process. CTA button: accent background.
2. **Hero** — full viewport height, dark background. Split grid: left = content (eyebrow "SYS.INIT // AGENT SANDBOX v0.4.1" with red blinking dot, huge title "TradingHunter" with glitch effect, subtitle, 2 buttons), right = ASCII art terminal panel with live indicator. Canvas background with particle flow.
3. **About** — 2-column grid. Left: section label "001 / what_is_this", heading "An AI agent playground for trading strategies.", paragraph, code block. Right sidebar: 3 stat cards (∞ Sandbox iterations, 0 Real money at risk, 24/7 Agent runtime) with large accent numbers.
4. **Features** — Header row (title + section label "04 / modules"). 4-column grid of feature cards with SVG icons + name + description. Cards have `:hover { background: var(--green-pale); transform: translateY(-4px); }`.
5. **Terminal Section** — dark background. Section label "002 / live_agent_log". Terminal window with titlebar dots + typing animation (agent log stream).
6. **Algorithmic Showcase** — dark background. Section label "003 / agent_visualization". Heading + interactive particle canvas (mouse move influences flow field).
7. **Process** — 3-column grid. "Three steps to the hunt." Steps: 01 Design, 02 Train, 03 Compete. Each has large faded number, heading, text, ASCII art.
8. **Ticker** — dark bar, overflowing marquee animation (`animation: ticker-slide 22s linear infinite`). Price pairs + agent P&L.
9. **CTA** — accent red background. Eyebrow "005 / init_arena", huge heading "Start your hunt.", subtitle, dark CTA button `▶ ./run_sandbox`. Grid overlay pattern + ASCII art watermark.
10. **Footer** — dark bar, copyright + version + 4 links.

**Animations on Home**:
- Glitch text on hero title (keyframes: `glitch-1`, `glitch-2`)
- Scroll reveal: elements with `.reveal` fade in + slide up (`opacity 0→1, translateY 24px→0`)
- Terminal typing: characters appear one by one with delays (25ms prompt, 8ms dim, 12ms others)
- Particle canvas: hero background + interactive flow field in algo section
- Ticker marquee: infinite horizontal slide

### 4.2 Arena Dashboard (`/arena`, `/arena/:id`)

Reference: `tradinghunter-sandbox-dashboard.html` (dark mode, full-height app)

**Layout**: Fixed-height app shell (100vh/dvh), grid rows:
```
topbar: 48px
ticker: 32px
main content: 1fr (fills remaining)
terminal: 180px
```

**Main content** is 3 columns:
```
left panel: 280px  |  center (chart): 1fr  |  right panel: 300px
```

**Topbar** (`48px`, dark):
- Left: Logo (`>_` prefix + "Trading" + "Hunter" with accent)
- Center: Nav tabs — sandbox, agents, arena, evolution, docs (active tab has green border + highlight)
- Right: LIVE indicator (green blinking dot) + AGENT #ID (amber)

**Ticker** (`32px`, dark): Scrolling marquee with price pairs (▲ green for up, ▼ red for down).

**Left Panel** (config sidebar):
1. Panel header: "agent_config" label + close button
2. Agent selector: `<select>` dropdown
3. Strategy section: 2×2 grid of strategy buttons (momentum, mean_rev, breakout, custom)
4. Parameters section: 3 sliders (EMA Period, RSI Period, ATR Mult.) with live value display
5. Risk management section: 4 text inputs (Max Drawdown %, Position Size %, Stop Loss %, Take Profit %)
6. Execution section: 3 toggles (Paper Trading, Auto-restart, Sound Alerts)
7. Deploy button: full-width green (`▶ deploy agent`), turns red when running (`■ stop agent`)

**Center (Chart)**:
- Toolbar: pair name + price (large, white), change badge (green border if up, red if down), timeframe buttons (1m, 5m, 15m, 1H, 4H, 1D)
- Chart area: dark canvas (`#080808`), candlestick chart with EMA overlay, volume bars, current price line with tag
- Chart overlay (top-left): EMA, RSI, ATR, VOL values

**Right Panel** (stats sidebar):
1. PnL section: "unrealized P&L" label, large green number, sparkline canvas, sub-text (% on capital)
2. Positions section: header + 3-column grid rows (pair, size, P&L) with green/red coloring
3. Signals section: scrollable list of signal items with colored dots (green=buy, red=sell, amber=warn), time, text, type badge

**Terminal** (bottom, `180px`):
- Header: terminal dots (r/y/g) + tab name "agent_log" + session ID
- Output area: scrollable log with colored lines (prompt=green, success=green, warn=amber, error=red, dim=dim green, white=white)
- Input line: `>` prompt + text input

**Responsive Behavior** (from the HTML, follow EXACTLY):
- **≥901px**: All 3 panels visible, mobile tabs hidden, mobile menu hidden
- **≤1200px**: Narrower columns (240px / 1fr / 260px)
- **≤900px**: Single column layout. Mobile tabs appear for switching between chart/config/positions/signals. Only one panel visible at a time (controlled by `.mobile-active`). Right panel moves below.
- **≤640px**: Topbar nav hidden (mobile menu hamburger shown), agent ID hidden, smaller fonts throughout, ticker text 9px, chart toolbar compact, PnL 24px, terminal 10px
- **≤380px**: Strategy grid becomes single column, smallest timeframe buttons, PnL 20px

### 4.3 Agent Profile (`/agents/:id`)

Reference: Dark mode design tokens from dashboard. Use `tradinghunter-docs.html` layout patterns (sidebar + main content) as structural reference.

**Layout**: Dark app shell with topbar + main content area.

**Content sections**:
1. Agent header: name, persona badge, ERC-8004 NFT info, status indicator (live/stopped)
2. Performance stats cards: total PnL, Sharpe ratio, win rate, total trades — use `--font-display` large numbers
3. PnL Chart: recharts LineChart with green/red coloring, dark background, green grid lines
4. Trade history table: sortable columns, monospace numbers, green for profit rows
5. Reputation tags: small bordered labels from ERC-8004 feedback

**Design tokens**: Use dark mode palette. Cards: `background: var(--bg-panel)`, `border: 1.5px solid var(--border-dark)`.

### 4.4 Leaderboard (`/leaderboard`)

Reference: Dark mode tokens. Table patterns from `tradinghunter-docs.html`.

**Content**:
1. Session filter: `<select>` dropdown with arena session IDs
2. Ranked table: columns — Rank (# with medal emoji for top 3), Agent (name + short ID), PnL (green/red), Sharpe, Win Rate, Trades
3. Sortable columns: click header to sort
4. Top performers cards: highlighted top 3 above the table

---

## 5. Component Specifications

### 5.1 Navbar (App-wide)

Two variants:
- **Landing Nav** (Home page): light mode dark bar, links scroll to sections, CTA button
- **Dashboard Nav** (all app pages): dark mode topbar, 48px height, nav tabs, LIVE indicator

### 5.2 AgentCard

Used in: Arena page, Home featured agents.

```tsx
// Anatomy:
<Card border={1.5px solid var(--border-dark)} background={var(--bg-panel)}>
  <CardHeader>
    <LiveIndicator running={isRunning} />  // green blinking dot + "LIVE" text
    <AgentName />                         // monospace, green-light
    <PersonaBadge />                      // small bordered tag
  </CardHeader>
  <PnLValue value={pnl} />               // font-display, large, green/red
  <MetricsRow>                            // small monospace stats
    <Metric label="Sharpe" value={sharpe} />
    <Metric label="Win Rate" value={winRate} />
    <Metric label="Trades" value={trades} />
  </MetricsRow>
</Card>
```

### 5.3 TradeFeed

Used in: Arena page right panel.

A scrolling list of trade events received via WebSocket. Each item has:
- Colored dot (green=buy, red=sell, amber=warn)
- Time (monospace, dim green, 9px)
- Description text (10px, gray)
- Type badge (bordered, colored text, 8px uppercase)

Maximum height should be constrained; auto-scroll to bottom on new items.

### 5.4 ArenaRing

Visual battle between agents. Animated bar chart using framer-motion:
- Each agent = one bar
- Bar height = proportional to PnL
- Color: green for positive, red for negative
- Animate on mount: height 0 → target height, duration 0.8s, ease "easeOut"
- Labels below: medal emoji (gold/silver/bronze), PnL value, agent short ID

### 5.5 PnLChart (recharts)

Equity curve line chart:
- Dark background (`#080808`)
- Grid lines: `rgba(26,58,26,0.3)`
- Line color: `#33ff33` (green) for positive territory, `#C44545` (red) for negative
- Area fill: gradient from line color to transparent (opacity 0.08)
- Tooltip: dark background, monospace font, green text
- Axis labels: monospace, 10px, `#1a8a1a`
- Responsive: resize on container width change

### 5.6 LeaderboardTable

Sortable table component:
- Header row: dark background, uppercase, 10px, green-terminal color
- Data rows: border-bottom 1px solid `rgba(26,58,26,0.5)`, hover background `rgba(51,255,51,0.02)`
- Rank column: medal emoji for 1-3
- PnL column: green for positive, red for negative, monospace
- Sort indicator: arrow in header on active sort column

### 5.7 Terminal

Reusable terminal component (used in Arena bottom bar):
- Dark background (`var(--fg-dark)`)
- Title bar: 3 colored dots (r/y/g) + title text + optional status
- Output: auto-scrolling, colored lines by type
- Input: `>` prompt + text input field
- Support commands typed by user (optional — for demo mode)
- Monospace font, 11-12px, line-height 1.7

### 5.8 Ticker

Reusable scrolling ticker bar:
- Dark background (`#080808`)
- Horizontal overflow hidden
- Inner content: `animation: ticker-slide 30s linear infinite`
- Items: price pairs with ▲/▼, separator `│`, spaced 32px apart
- Font: 10px, uppercase, letter-spacing 0.12em
- Green for up, red for down

---

## 6. WebSocket Integration

### 6.1 useWebSocket Hook

```ts
function useWebSocket(url: string): {
  lastMessage: MessageEvent | null;
  readyState: number;
  sendMessage: (data: string) => void;
}
```

Used on `/arena` for real-time trade events. Reconnects on disconnect.

### 6.2 useContractEvents Hook

Listens to `TradeExecuted` events from TradeRegistry contract via wagmi's `useWatchContractEvent`.

Returns: `TradeEvent[]` — array of recent events (max 100).

### 6.3 Event Flow

```
Backend WebSocket → useWebSocket → TradeFeed (scrolling list)
                                   → AgentCard (live PnL update)
                                   → PnLChart (new data point)
Contract Events  → useContractEvents → on-chain confirmation badges
```

---

## 7. Wallet Connection

- Use wagmi `useAccount` + `useConnect` for Mantle Sepolia (chain 5003)
- Required for: viewing owned agent NFTs, submitting reputation feedback
- Not required for: leaderboard, trade feed, arena view (read-only)
- Connect button in topbar (dashboard) or nav (landing)

---

## 8. Responsive Breakpoints

Follow the breakpoints from the HTML designs:

| Breakpoint | Target |
|---|---|
| `max-width: 1200px` | Narrower arena panels |
| `max-width: 1024px` | Landing: hero 1-col, about 1-col, features 2-col |
| `max-width: 900px` | Dashboard: single col + mobile tabs |
| `max-width: 768px` | Docs: sidebar hidden, mobile toggle |
| `max-width: 640px` | Dashboard: full mobile, hamburger menu |
| `max-width: 480px` | Docs: reduced font sizes |
| `max-width: 380px` | Smallest: single-col grids everywhere |

**Key responsive rules**:
- Use `clamp()` for fluid typography (hero titles, stat numbers, section headings)
- No horizontal overflow at any breakpoint
- Test viewports: 360×800, 390×844, 430×932, 600×960, 820×1180, 1024×768, 1366×768, 1440×900, 1920×1080

---

## 9. Animation Specifications

All animations must use framer-motion for React components, matching these CSS reference values:

| Animation | Duration | Easing | Reference |
|---|---|---|---|
| Bar grow (ArenaRing) | 0.8s | easeOut | `transition={{ duration: 0.8, ease: "easeOut" }}` |
| Scroll reveal | 0.6s | ease | `initial={{ opacity: 0, y: 24 }}` → `animate={{ opacity: 1, y: 0 }}` |
| Glitch text | 4s loop | — | CSS keyframes glitch-1 / glitch-2 |
| Blinking cursor | 1s | step-end | `animate={{ opacity: [1,1,0,0] }}` with step timing |
| Blinking dot | 1s / 1.5s | — | `animate={{ opacity: [1,0.3,1] }}` |
| Ticker marquee | 22s–30s | linear infinite | CSS animation (or framer-motion `animate={{ x: ["0%", "-50%"] }}`) |
| Terminal typing | 8–25ms per char | — | setTimeout-based character reveal |
| Hover lift | 0.15s | — | `whileHover={{ y: -2 }}` or CSS `transform 0.15s` |
| Particle flow | continuous | — | Canvas `requestAnimationFrame` (not framer-motion) |

---

## 10. Implementation Rules for AI Agents

When working on the frontend, follow these rules in order:

1. **Match the HTML designs first** — before inventing anything new, check if a component/pattern exists in the 3 HTML files
2. **Extract tokens before coding** — every color, font, spacing, and border must use the CSS variables defined above. Never hardcode colors.
3. **Build from largest layout down** — start with page grid, then panels, then individual components
4. **Implement all states** — default, hover, focus, active, disabled, loading, empty, error, success
5. **Test responsive** — validate at the 9 viewport sizes listed above, no horizontal overflow
6. **Keep surfaces separate** — landing page vs dashboard vs docs are distinct routes/surfaces
7. **No generic cards** — each component has a specific purpose and layout from the design
8. **Preserve the terminal aesthetic** — sharp borders (no radius), monospace fonts, scanlines, green-on-dark palette
9. **Canvas effects are part of the design** — hero particle flow and algo flow field are not decorative; they're specified interactions
10. **When in doubt, read the HTML source** — the 3 design files are the final authority

---

## 11. Files Checklist for Implementation

| File | Status | Design Reference |
|---|---|---|
| `src/styles/global.css` | Needs rewrite | Extract all tokens from HTML `<style>` blocks |
| `src/main.tsx` | Exists | Wire providers correctly |
| `src/App.tsx` | Exists | Update routes |
| `src/pages/Home.tsx` | Needs rewrite | `landingpage.html` (hero → footer, all sections) |
| `src/pages/Arena.tsx` | Needs rewrite | `sandbox-dashboard.html` (full app shell) |
| `src/pages/AgentProfile.tsx` | Needs rewrite | Dark mode tokens + docs page structure |
| `src/pages/Leaderboard.tsx` | Needs rewrite | Dark mode table from docs page |
| `src/components/Navbar.tsx` | Create | Two variants: landing nav + dashboard topbar |
| `src/components/AgentCard.tsx` | Needs rewrite | Dashboard left panel patterns |
| `src/components/TradeFeed.tsx` | Needs rewrite | Dashboard signals section |
| `src/components/ArenaRing.tsx` | Needs rewrite | framer-motion bars matching design |
| `src/components/PnLChart.tsx` | Needs rewrite | recharts matching chart canvas specs |
| `src/components/LeaderboardTable.tsx` | Needs rewrite | Docs page table patterns |
| `src/components/Terminal.tsx` | Create | Dashboard terminal component |
| `src/components/Ticker.tsx` | Create | Ticker marquee (used on Home + Arena) |
| `src/hooks/useWebSocket.ts` | Exists | Verify reconnect logic |
| `src/hooks/useContractEvents.ts` | Exists | Fix TS errors (already done) |
| `src/lib/contracts.ts` | Exists | Verify ABIs + addresses |
| `src/lib/api.ts` | Exists | Verify endpoint URLs |
