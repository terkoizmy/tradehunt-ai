import { useEffect, useState } from "react";
import { fetchSessions, fetchLeaderboard, Session, Score } from "../lib/api";
import LeaderboardTable from "../components/LeaderboardTable";

export default function Leaderboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [scores, setScores] = useState<Score[]>([]);

  useEffect(() => {
    fetchSessions().then((data) => {
      setSessions(data);
      if (data.length > 0) {
        setSelectedId(data[0].id);
      }
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    fetchLeaderboard(selectedId).then(setScores).catch(console.error);
  }, [selectedId]);

  return (
    <div>
      <section className="section">
        <h1>Leaderboard</h1>
      </section>

      <section className="section">
        <div style={{ marginBottom: 24 }}>
          <label className="muted" style={{ marginRight: 8 }}>
            Session:
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            style={{
              background: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              padding: "8px 16px",
              borderRadius: 6,
              fontFamily: "var(--font-mono)",
              fontSize: 14,
            }}
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.status})
              </option>
            ))}
          </select>
        </div>

        {scores.length === 0 ? (
          <p className="muted">No scores for this session yet.</p>
        ) : (
          <LeaderboardTable scores={scores} />
        )}
      </section>
    </div>
  );
}
