import { Link } from "react-router-dom";
import type { Agent } from "../lib/api";

interface Props {
  agent: Agent;
  live?: boolean;
}

const PERSONA_COLORS: Record<string, string> = {
  aggressive: "var(--accent-red)",
  conservative: "var(--accent-green)",
  sentiment: "var(--accent-yellow)",
  arbitrageur: "var(--accent-blue)",
};

const PERSONA_EMOJI: Record<string, string> = {
  aggressive: "Bull",
  conservative: "Turtle",
  sentiment: "Oracle",
  arbitrageur: "Sniper",
};

export default function AgentCard({ agent, live }: Props) {
  const color = PERSONA_COLORS[agent.persona] || "var(--accent-blue)";
  const emoji = PERSONA_EMOJI[agent.persona] || "Bot";

  return (
    <Link
      to={`/agents/${agent.id}`}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <div
        className="card"
        style={{
          borderColor: live ? color : "var(--border)",
          transition: "border-color 0.3s",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <div>
            <h3>{agent.name}</h3>
            <p className="muted" style={{ fontSize: 13, marginTop: 2 }}>
              {emoji} · {agent.persona}
            </p>
          </div>
          <span className={`badge badge-${agent.status === "running" ? "green" : "blue"}`}>
            {agent.status === "running" ? "● LIVE" : agent.status}
          </span>
        </div>

        {agent.onchain_id && (
          <p className="muted" style={{ fontSize: 11, marginTop: 12 }}>
            ERC-8004 #{agent.onchain_id}
          </p>
        )}

        <div
          style={{
            marginTop: 16,
            padding: "8px 0",
            borderTop: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span className="muted" style={{ fontSize: 11 }}>
            {agent.wallet_address.slice(0, 6)}...{agent.wallet_address.slice(-4)}
          </span>
          {live && (
            <span style={{ color, fontSize: 11, fontFamily: "var(--font-mono)" }}>
              LIVE
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
