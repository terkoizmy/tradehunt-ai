import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchAgent, fetchTrades, Agent, Trade } from "../lib/api";
import PnLChart from "../components/PnLChart";

export default function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    if (!id) return;
    fetchAgent(id).then(setAgent).catch(console.error);
    fetchTrades(id, undefined, 100).then(setTrades).catch(console.error);
  }, [id]);

  if (!agent) {
    return <p className="muted">Loading agent...</p>;
  }

  const totalPnl = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);
  const winCount = trades.filter((t) => (t.pnl || 0) > 0).length;
  const winRate = trades.length > 0 ? (winCount / trades.length) * 100 : 0;

  return (
    <div>
      <Link to="/arena" className="muted" style={{ fontSize: 14 }}>
        ← Back to Arena
      </Link>

      <section className="section" style={{ marginTop: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <h1>{agent.name}</h1>
          <span className={`badge badge-${agent.status === "running" ? "green" : "blue"}`}>
            {agent.status}
          </span>
        </div>
        <div style={{ display: "flex", gap: 24, marginTop: 8 }}>
          <span className="muted" style={{ fontSize: 13 }}>
            Persona: <strong>{agent.persona}</strong>
          </span>
          <span className="muted" style={{ fontSize: 13 }}>
            Wallet:{" "}
            <code style={{ fontSize: 12 }}>
              {agent.wallet_address.slice(0, 6)}...{agent.wallet_address.slice(-4)}
            </code>
          </span>
          {agent.onchain_id && (
            <span className="muted" style={{ fontSize: 13 }}>
              ERC-8004 ID: <strong>#{agent.onchain_id}</strong>
            </span>
          )}
        </div>
      </section>

      <section className="section">
        <div className="grid-4">
          <div className="card" style={{ textAlign: "center" }}>
            <div className={`stat-value ${totalPnl >= 0 ? "positive" : "negative"}`}>
              {totalPnl >= 0 ? "+" : ""}
              {totalPnl.toFixed(2)} USDT
            </div>
            <div className="stat-label">Total PnL</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div className="stat-value">{trades.length}</div>
            <div className="stat-label">Total Trades</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div className="stat-value">{winRate.toFixed(1)}%</div>
            <div className="stat-label">Win Rate</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div className="stat-value">
              {agent.created_at ? new Date(agent.created_at).toLocaleDateString() : "N/A"}
            </div>
            <div className="stat-label">Registered</div>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>PnL Curve</h2>
        <div className="card">
          <PnLChart trades={trades} />
        </div>
      </section>

      <section className="section">
        <h2>Trade History</h2>
        {trades.length === 0 ? (
          <p className="muted">No trades yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Price</th>
                  <th>Qty</th>
                  <th>PnL</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t) => (
                  <tr key={t.id}>
                    <td className="muted">
                      {t.created_at ? new Date(t.created_at).toLocaleTimeString() : ""}
                    </td>
                    <td>{t.symbol}</td>
                    <td className={t.side === "buy" ? "positive" : "negative"}>
                      {t.side.toUpperCase()}
                    </td>
                    <td>{t.price.toFixed(2)}</td>
                    <td>{t.quantity.toFixed(4)}</td>
                    <td className={(t.pnl || 0) >= 0 ? "positive" : "negative"}>
                      {t.pnl !== null ? `${t.pnl >= 0 ? "+" : ""}${t.pnl.toFixed(2)}` : "-"}
                    </td>
                    <td>
                      {t.confidence !== null ? `${(t.confidence * 100).toFixed(0)}%` : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
