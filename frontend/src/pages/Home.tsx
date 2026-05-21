import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAgents, fetchSessions, Agent, Session } from "../lib/api";
import AgentCard from "../components/AgentCard";

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    fetchAgents().then(setAgents).catch(console.error);
    fetchSessions().then(setSessions).catch(console.error);
  }, []);

  const runningAgents = agents.filter((a) => a.status === "running");

  return (
    <div>
      <section className="section">
        <h1>AI Trading Arena</h1>
        <p className="muted" style={{ fontSize: 16, maxWidth: 600 }}>
          Watch AI quant agents with distinct personas compete in real-time.
          Every trade is logged on-chain via ERC-8004 agent identity.
        </p>
        <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
          <Link to="/arena" className="btn">
            Enter Arena
          </Link>
          <Link to="/leaderboard" className="btn">
            View Leaderboard
          </Link>
        </div>
      </section>

      <section className="section">
        <h2>Active Agents ({runningAgents.length})</h2>
        {runningAgents.length === 0 ? (
          <p className="muted">No agents running. Start one from the CLI.</p>
        ) : (
          <div className="grid-3">
            {runningAgents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </section>

      <section className="section">
        <h2>All Registered Agents</h2>
        {agents.length === 0 ? (
          <p className="muted">No agents registered yet.</p>
        ) : (
          <div className="grid-3">
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </section>

      <section className="section">
        <h2>Recent Sessions</h2>
        {sessions.length === 0 ? (
          <p className="muted">No arena sessions yet.</p>
        ) : (
          <div className="grid-2">
            {sessions.slice(0, 4).map((s) => (
              <div key={s.id} className="card">
                <h3>{s.name}</h3>
                <p className="muted" style={{ fontSize: 13 }}>
                  Status:{" "}
                  <span className={`badge badge-${s.status === "active" ? "green" : "blue"}`}>
                    {s.status}
                  </span>
                </p>
                <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                  {s.start_time ? new Date(s.start_time).toLocaleString() : "Not started"}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
