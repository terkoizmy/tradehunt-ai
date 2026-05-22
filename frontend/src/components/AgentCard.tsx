import { Link } from "react-router-dom";
import type { Agent } from "../lib/api";

interface Props {
  agent: Agent;
  live?: boolean;
  pnl?: number;
}

const PERSONA_BADGES: Record<string, { label: string; emoji: string }> = {
  aggressive: { label: "aggressive", emoji: "Bull" },
  conservative: { label: "conservative", emoji: "Turtle" },
  sentiment: { label: "sentiment", emoji: "Oracle" },
  arbitrageur: { label: "arbitrageur", emoji: "Sniper" },
};

export default function AgentCard({ agent, live, pnl }: Props) {
  const persona = PERSONA_BADGES[agent.persona] || {
    label: agent.persona,
    emoji: "Bot",
  };

  const isRunning = agent.status === "running" || agent.status === "online";

  return (
    <Link
      to={`/agents/${agent.id}`}
      style={{ textDecoration: "none", color: "inherit", display: "block" }}
    >
      <div
        className="card"
        style={{
          border: live
            ? "1.5px solid var(--green-terminal)"
            : "1.5px solid var(--border-dark)",
          padding: "16px 20px",
          transition: "border-color 0.3s",
          cursor: "pointer",
        }}
      >
        {/* Header row */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 12,
          }}
        >
          <div style={{ minWidth: 0, flex: 1 }}>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "18px",
                color: "var(--surface)",
                lineHeight: 1.1,
                marginBottom: 6,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {agent.name}
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  padding: "2px 8px",
                  border: "1px solid var(--green-terminal)",
                  color: "var(--green-terminal)",
                  fontFamily: "var(--font-body)",
                }}
              >
                {persona.label}
              </span>
              <span
                style={{
                  fontSize: 10,
                  color: "var(--green-dim)",
                  fontFamily: "var(--font-body)",
                }}
              >
                {agent.onchain_id
                  ? `Token ID: ${agent.onchain_id}`
                  : "Off-chain"}
              </span>
            </div>
          </div>

          {/* Status */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              fontSize: 10,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: isRunning ? "var(--green-terminal)" : "var(--red-light)",
              flexShrink: 0,
              marginLeft: 8,
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                background: isRunning
                  ? "var(--green-terminal)"
                  : "var(--red)",
                animation: isRunning ? "blink-dot 1s infinite" : "none",
              }}
            />
            {isRunning ? "live" : "stopped"}
          </div>
        </div>

        {/* PnL display when live */}
        {live && pnl !== undefined && (
          <div style={{ marginBottom: 12 }}>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(24px, 3vw, 36px)",
                lineHeight: 1,
                color: pnl >= 0 ? "var(--green-terminal)" : "var(--red-light)",
              }}
            >
              {pnl >= 0 ? "+" : ""}
              {pnl.toFixed(2)} USDT
            </div>
          </div>
        )}

        {/* Metrics row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 12,
            borderTop: "1px solid rgba(26,58,26,0.5)",
            paddingTop: 10,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 2,
              }}
            >
              sharpe
            </div>
            <div
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 12,
                color: "var(--surface)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              —
            </div>
          </div>
          <div>
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 2,
              }}
            >
              win rate
            </div>
            <div
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 12,
                color: "var(--surface)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              —
            </div>
          </div>
          <div>
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 2,
              }}
            >
              trades
            </div>
            <div
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 12,
                color: "var(--surface)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              —
            </div>
          </div>
        </div>

        {/* Wallet */}
        <div
          style={{
            marginTop: 10,
            fontSize: 10,
            color: "var(--green-dim)",
            fontFamily: "var(--font-body)",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {agent.wallet_address.slice(0, 8)}…
          {agent.wallet_address.slice(-6)}
        </div>
      </div>
    </Link>
  );
}
