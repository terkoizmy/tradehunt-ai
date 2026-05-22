import { useEffect, useState } from "react";
import { fetchAgents, fetchTrades, fetchLeaderboard, Agent, Trade } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import AgentCard from "../components/AgentCard";
import ArenaRing from "../components/ArenaRing";
import TradeFeed from "../components/TradeFeed";

interface WsTradeMessage {
  readonly type: "trade";
  agent_id: string;
  action: string;
  symbol: string;
  price: number;
  quantity: number;
  pnl: number | null;
  reasoning?: string;
}

interface WsPnlMessage {
  readonly type: "pnl_update";
  agent_id: string;
  symbol: string;
  pnl: number;
}

interface WsAgentStatusMessage {
  readonly type: "agent_status";
  agent_id: string;
  status: string;
}

interface WsAgentRegisteredMessage {
  readonly type: "agent_registered";
  agent_id: string;
  name: string;
  persona: string;
}

type WsMessage =
  | WsTradeMessage
  | WsPnlMessage
  | WsAgentStatusMessage
  | WsAgentRegisteredMessage;

export default function Arena() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [scores, setScores] = useState<import("../lib/api").Score[]>([]);
  const [livePnL, setLivePnL] = useState<Record<string, number>>({});

  const { data: wsMsg, connected: wsConnected } = useWebSocket<WsMessage>(
    "ws://localhost:8000/ws/trades"
  );

  // Load initial data
  useEffect(() => {
    fetchAgents().then(setAgents).catch(console.error);
    fetchTrades(undefined, undefined, 20).then(setTrades).catch(console.error);

    // Fetch latest session scores for ArenaRing
    fetch("http://localhost:8000/api/arena/sessions")
      .then((r) => r.json())
      .then((sessions: import("../lib/api").Session[]) => {
        const active = sessions.find((s) => s.status === "active");
        if (active) {
          fetchLeaderboard(active.id).then(setScores).catch(console.error);
        }
      })
      .catch(console.error);
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (!wsMsg) return;

    switch (wsMsg.type) {
      case "trade": {
        const t: Trade = {
          id: `${Date.now()}-${Math.random()}`,
          agent_id: wsMsg.agent_id,
          symbol: wsMsg.symbol,
          side: wsMsg.action.toLowerCase(),
          price: wsMsg.price,
          quantity: wsMsg.quantity,
          pnl: wsMsg.pnl,
          confidence: null,
          reasoning: wsMsg.reasoning ?? null,
          tx_hash: null,
          created_at: new Date().toISOString(),
        };
        setTrades((prev) => [t, ...prev].slice(0, 100));
        break;
      }
      case "pnl_update": {
        setLivePnL((prev) => ({
          ...prev,
          [wsMsg.agent_id]: wsMsg.pnl,
        }));
        break;
      }
      case "agent_status": {
        const agentId = wsMsg.agent_id;
        const newStatus = wsMsg.status;
        setAgents((prev) =>
          prev.map((a) => (a.id === agentId ? { ...a, status: newStatus } : a))
        );
        break;
      }
      case "agent_registered": {
        const newAgent: Agent = {
          id: wsMsg.agent_id,
          name: wsMsg.name,
          persona: wsMsg.persona,
          wallet_address: "0x0000...0000",
          status: "online",
          onchain_id: null,
          created_at: new Date().toISOString(),
        };
        setAgents((prev) => {
          const exists = prev.some((a) => a.id === newAgent.id);
          return exists ? prev : [newAgent, ...prev];
        });
        break;
      }
      default:
        break;
    }
  }, [wsMsg]);

  const running = agents.filter(
    (a) => a.status === "running" || a.status === "online"
  );
  const idle = agents.filter(
    (a) => a.status !== "running" && a.status !== "online"
  );

  return (
    <div>
      {/* Header */}
      <section style={{ marginBottom: 32 }}>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(28px, 4vw, 40px)",
            color: "var(--surface)",
            lineHeight: 1.05,
            marginBottom: 8,
          }}
        >
          Live Arena
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            color: "var(--green-dim)",
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              background: wsConnected
                ? "var(--green-terminal)"
                : "var(--red)",
              animation: wsConnected ? "blink-dot 1s infinite" : "none",
            }}
          />
          {wsConnected ? `${running.length} agents trading` : "disconnected — reconnecting..."}
          · Real-time WebSocket feed
        </div>
      </section>

      {/* Main layout: arena content + trade feed */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 360px",
          gap: 24,
          alignItems: "start",
        }}
      >
        <div>
          {/* Arena Ring — battle visualization */}
          {scores.length > 0 && (
            <section style={{ marginBottom: 32 }}>
              <ArenaRing scores={scores} />
            </section>
          )}

          {/* Live Agents */}
          <section style={{ marginBottom: 32 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 16,
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.18em",
                  color: "var(--green-dim)",
                }}
              >
                {'>'}
              </span>
              <span
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.15em",
                  color: "var(--green-dim)",
                }}
              >
                competing_agents
              </span>
              <span
                style={{
                  fontSize: 10,
                  color: "var(--green-terminal)",
                  marginLeft: "auto",
                }}
              >
                {running.length}
              </span>
            </div>

            {running.length === 0 ? (
              <div
                className="card"
                style={{
                  padding: "40px 32px",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 11,
                    color: "var(--green-dim)",
                    opacity: 0.15,
                    lineHeight: 1.1,
                    marginBottom: 24,
                    whiteSpace: "pre",
                  }}
                >
                  {`        ┌──────────────────────┐\n` +
                    `        │  ████          ████  │\n` +
                    `        │  ████          ████  │\n` +
                    `        │  ██████████████████  │\n` +
                    `        │  ██████████████████  │\n` +
                    `        │  ██    ██████    ██  │\n` +
                    `        │  ██  Z ██████ z  ██  │\n` +
                    `        │  ██    ██████    ██  │\n` +
                    `        │  ██████████████████  │\n` +
                    `        │  ██████████████████  │\n` +
                    `        │  ██  ██████████  ██  │\n` +
                    `        │  ██  ██████████  ██  │\n` +
                    `        │  ██              ██  │\n` +
                    `        │  ────────────────    │\n` +
                    `        └──────────────────────┘`}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(20px, 3vw, 28px)",
                    color: "var(--surface)",
                    marginBottom: 8,
                  }}
                >
                  No agents deployed
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 13,
                    color: "#888",
                    maxWidth: 400,
                    margin: "0 auto 24px",
                    lineHeight: 1.6,
                  }}
                >
                  Start an agent from the CLI to enter the arena:
                </div>
                <code
                  style={{
                    display: "inline-block",
                    background: "var(--fg-dark)",
                    border: "1px solid var(--border-dark)",
                    padding: "10px 16px",
                    color: "var(--green-terminal)",
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                  }}
                >
                  cd agents && python -m src.main --persona aggressive
                </code>
              </div>
            ) : (
              <div className="grid-2">
                {running.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    live
                    pnl={livePnL[agent.id]}
                  />
                ))}
              </div>
            )}
          </section>

          {/* Benched Agents */}
          {idle.length > 0 && (
            <section style={{ marginBottom: 32 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  marginBottom: 16,
                }}
              >
                <span
                  style={{
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: "0.18em",
                    color: "var(--green-dim)",
                  }}
                >
                  {'>'}
                </span>
                <span
                  style={{
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: "0.15em",
                    color: "var(--green-dim)",
                  }}
                >
                  benched_agents
                </span>
                <span
                  style={{
                    fontSize: 10,
                    color: "var(--green-dim)",
                    marginLeft: "auto",
                  }}
                >
                  {idle.length}
                </span>
              </div>
              <div className="grid-2">
                {idle.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Trade Feed sidebar */}
        <div style={{ position: "sticky", top: 20 }}>
          <TradeFeed trades={trades} connected={wsConnected} />
        </div>
      </div>
    </div>
  );
}
