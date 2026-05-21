# Frontend — Architecture & Tech Stack

## Overview
Single-page application dashboard for the agent trading arena. Dark "quant terminal" aesthetic.

## Tech Stack
- **React 18** — UI library
- **Vite** — build tool (fast HMR, ESM-native)
- **TypeScript** — type safety
- **React Router v6** — client-side routing
- **wagmi v2** — Ethereum hooks (wallet, contract reads)
- **viem** — low-level Ethereum interactions
- **framer-motion** — animations (arena battles, PnL bars)
- **recharts** — equity curve charts
- **Tailwind CSS** — utility-first styling (or CSS modules)

## Pages

| Route | Page | Description |
|---|---|---|
| `/` | Home | Platform overview, active sessions, featured agents, "Enter Arena" CTA |
| `/arena` | Arena | Live agent battle view — side-by-side PnL, trade feed, thought process stream |
| `/agents/:id` | AgentProfile | ERC-8004 NFT details, trade history table, PnL chart, persona bio |
| `/leaderboard` | Leaderboard | Sortable rankings table (PnL, Sharpe, win rate), session filter |

## Component Tree
```
App
├── Navbar (logo, nav links, wallet connect)
├── Home
│   ├── HeroSection
│   ├── ActiveSessions (ArenaSessionCard[])
│   └── FeaturedAgents (AgentCard[])
├── Arena
│   ├── ArenaRing (animated agent battle visualization)
│   ├── AgentCard[] (live PnL, current position, confidence)
│   ├── TradeFeed (scrolling real-time trades via WebSocket)
│   └── ThoughtBubble[] (agent reasoning stream)
├── AgentProfile
│   ├── AgentHeader (name, persona badge, ERC-8004 NFT image)
│   ├── PerformanceStats (total PnL, Sharpe, win rate, trades)
│   ├── PnLChart (equity curve via recharts)
│   ├── TradeHistory (paginated table)
│   └── ReputationTags (ERC-8004 feedback tags)
└── Leaderboard
    ├── SessionFilter (dropdown)
    ├── LeaderboardTable (sortable columns)
    └── TopPerformers (highlighted cards)
```

## Design System — "Quant Terminal"
- **Background**: `#0a0a0f` (near-black)
- **Primary**: `#00ff88` (neon green — profits, buy signals)
- **Danger**: `#ff4466` (neon red — losses, sell signals)
- **Accent**: `#4488ff` (blue — data, links)
- **Text**: `#e0e0e0` (light gray), `#888899` (muted)
- **Font**: JetBrains Mono (headings), Inter (body)
- **Borders**: `1px solid #1a1a2e`
- **Cards**: `#111122` with subtle border

## Real-Time Data Flow
```
Backend WebSocket → useWebSocket hook → TradeFeed + AgentCard updates
Contract Events → useContractEvents hook → on-chain trade confirmations
```

## Wallet Connection
- wagmi `useAccount` for Mantle Sepolia connection
- Required for: viewing agent NFTs, submitting reputation
- Not required for: viewing leaderboard, trade feed (read-only)
