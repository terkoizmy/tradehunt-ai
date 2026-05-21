import { useEffect, useState } from "react";
import { fetchAgents, fetchTrades, Agent, Trade } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";
import AgentCard from "../components/AgentCard";
import TradeFeed from "../components/TradeFeed";

export default function Arena() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const { data: wsTrade } = useWebSocket<Trade>("ws://localhost:8000/ws/trades");

  useEffect(() => {
    fetchAgents().then(setAgents).catch(console.error);
    fetchTrades(undefined, undefined, 20).then(setTrades).catch(console.error);
  }, []);

  useEffect(() => {
    if (wsTrade) {
      setTrades((prev) => [wsTrade, ...prev.slice(0, 99)]);
    }
  }, [wsTrade]);

  const running = agents.filter((a) => a.status === "running");
  const idle = agents.filter((a) => a.status === "idle");

  return (
    <div>
      <section className="section">
        <h1>Live Arena</h1>
        <p className="muted">
          {running.length} agents trading · Real-time WebSocket feed
        </p>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 24 }}>
        <div>
          <section className="section">
            <h2>Competing Agents</h2>
            {running.length === 0 ? (
              <div className="card">
                <p className="muted">
                  No agents running. Start agents from the CLI:
                  <br />
                  <code style={{ color: "var(--accent-green)" }}>
                    cd agents && python -m src.main --persona aggressive
                  </code>
                </p>
              </div>
            ) : (
              <div className="grid-2">
                {running.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} live />
                ))}
              </div>
            )}
          </section>

          <section className="section">
            <h2>Benched Agents</h2>
            {idle.length === 0 ? (
              <p className="muted">No idle agents.</p>
            ) : (
              <div className="grid-2">
                {idle.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </div>
            )}
          </section>
        </div>

        <div>
          <TradeFeed trades={trades} />
        </div>
      </div>
    </div>
  );
}
