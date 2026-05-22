import { useEffect, useState } from "react";
import { fetchSessions, fetchLeaderboard, Session, Score } from "../lib/api";
import LeaderboardTable from "../components/LeaderboardTable";

export default function Leaderboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [scores, setScores] = useState<Score[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSessions()
      .then((data) => {
        setSessions(data);
        if (data.length > 0) {
          setSelectedId(data[0].id);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    fetchLeaderboard(selectedId)
      .then((data) => {
        setScores(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedId]);

  const selectedSession = sessions.find((s) => s.id === selectedId);

  // Top 3 podium cards
  const top3 = scores.slice(0, 3);
  const PODIUM_WIDTHS = [220, 200, 200];
  const PODIUM_COLORS = [
    "var(--amber)",
    "var(--green-dim)",
    "var(--accent)",
  ];
  const MEDALS = ["🥇", "🥈", "🥉"];

  return (
    <div>
      {/* Header */}
      <section style={{ marginBottom: 24 }}>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(28px, 4vw, 40px)",
            color: "var(--surface)",
            lineHeight: 1.05,
            marginBottom: 8,
          }}
        >
          Leaderboard
        </div>
      </section>

      {/* Session Selector */}
      <section
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "16px 0",
          borderBottom: "1.5px solid var(--border-dark)",
          marginBottom: 24,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            style={{
              background: "var(--fg-dark)",
              color: "var(--green-light)",
              border: "1.5px solid var(--border-dark)",
              padding: "8px 10px",
              fontFamily: "var(--font-body)",
              fontSize: 12,
              cursor: "pointer",
              appearance: "none",
              minWidth: 200,
            }}
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {selectedSession && (
          <>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: 10,
                textTransform: "uppercase",
                letterSpacing: "0.1em",
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  background:
                    selectedSession.status === "active"
                      ? "var(--green-terminal)"
                      : "var(--green-dim)",
                  animation:
                    selectedSession.status === "active"
                      ? "blink-dot 1s infinite"
                      : "none",
                }}
              />
              <span
                style={{
                  color:
                    selectedSession.status === "active"
                      ? "var(--green-terminal)"
                      : "var(--green-dim)",
                }}
              >
                {selectedSession.status === "active" ? "LIVE" : "ENDED"}
              </span>
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--green-dim)",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
              }}
            >
              {scores.length} agents
            </div>
            {selectedSession.start_time && (
              <div
                style={{
                  fontSize: 10,
                  color: "var(--green-dim)",
                }}
              >
                {new Date(selectedSession.start_time).toLocaleDateString()} —{" "}
                {selectedSession.end_time
                  ? new Date(selectedSession.end_time).toLocaleDateString()
                  : "Present"}
              </div>
            )}
          </>
        )}
      </section>

      {/* Top 3 Podium */}
      {top3.length > 0 && (
        <section
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 32,
            padding: "40px 0",
            flexWrap: "wrap",
          }}
        >
          {top3.map((s, i) => {
            const isPositive = s.total_pnl >= 0;
            return (
              <div
                key={s.agent_id}
                style={{
                  width: PODIUM_WIDTHS[i],
                  background: "var(--bg-panel)",
                  border: `2px solid ${PODIUM_COLORS[i]}`,
                  padding: "24px 20px",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: i === 0 ? 48 : 40, lineHeight: 1 }}>
                  {MEDALS[i]}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 22,
                    color: "var(--surface)",
                    marginTop: 12,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  Agent {s.agent_id.slice(0, 6)}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 36,
                    color: isPositive
                      ? "var(--green-terminal)"
                      : "var(--red-light)",
                    lineHeight: 1,
                    marginTop: 8,
                  }}
                >
                  {isPositive ? "+" : ""}
                  {s.total_pnl.toFixed(2)}%
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--green-dim)",
                    marginTop: 8,
                  }}
                >
                  Sharpe {s.sharpe_ratio?.toFixed(2) ?? "—"} · Win{" "}
                  {s.win_rate !== null
                    ? `${(s.win_rate * 100).toFixed(0)}`
                    : "—"}
                  % · {s.trade_count} trades
                </div>
              </div>
            );
          })}
        </section>
      )}

      {/* Rankings Table */}
      <section style={{ marginBottom: 40 }}>
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
              letterSpacing: "0.15em",
              color: "var(--green-dim)",
            }}
          >
            rankings
          </span>
        </div>

        {loading ? (
          <div
            className="card"
            style={{
              padding: 40,
              textAlign: "center",
              color: "var(--green-dim)",
            }}
          >
            Loading...
          </div>
        ) : scores.length === 0 ? (
          <div
            className="card"
            style={{
              padding: 40,
              textAlign: "center",
              color: "var(--green-dim)",
            }}
          >
            No scores for this session yet.
          </div>
        ) : (
          <LeaderboardTable scores={scores} />
        )}
      </section>
    </div>
  );
}
