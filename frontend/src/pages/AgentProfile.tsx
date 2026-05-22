import { useEffect, useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchAgent, fetchTrades, Agent, Trade } from "../lib/api";
import PnLChart from "../components/PnLChart";

const PAGE_SIZE = 20;

export default function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!id) return;
    fetchAgent(id).then(setAgent).catch(console.error);
    fetchTrades(id, undefined, 500)
      .then(setTrades)
      .catch(console.error);
    setPage(1);
  }, [id]);

  if (!agent) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 80,
          color: "var(--green-dim)",
        }}
      >
        Loading agent...
      </div>
    );
  }

  const totalPnl = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);
  const winCount = trades.filter((t) => (t.pnl || 0) > 0).length;
  const lossCount = trades.length - winCount;
  const winRate = trades.length > 0 ? (winCount / trades.length) * 100 : 0;

  // Pagination
  const totalPages = Math.ceil(trades.length / PAGE_SIZE);
  const paginatedTrades = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return trades.slice(start, start + PAGE_SIZE);
  }, [trades, page]);

  const isRunning = agent.status === "running" || agent.status === "online";

  return (
    <div>
      {/* Back link */}
      <div style={{ marginBottom: 16 }}>
        <Link
          to="/arena"
          style={{
            color: "var(--green-light)",
            textDecoration: "none",
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
          }}
        >
          ← Back to Arena
        </Link>
      </div>

      {/* Agent Header */}
      <section
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "24px 0",
          borderBottom: "2px solid var(--border-dark)",
          flexWrap: "wrap",
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: 48,
            height: 48,
            border: "2px solid var(--green-dim)",
            background: "var(--bg-dark)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 16,
            fontWeight: 700,
            color: "var(--green-terminal)",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            flexShrink: 0,
          }}
        >
          #{agent.id.slice(0, 2)}
        </div>

        {/* Info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "clamp(22px, 3vw, 28px)",
              color: "var(--surface)",
              lineHeight: 1.1,
              marginBottom: 8,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {agent.name}{" "}
            <span style={{ color: "var(--green-dim)", fontSize: 16 }}>
              #{agent.id.slice(0, 6)}
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
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
              {agent.persona}
            </span>
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontSize: 10,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: isRunning ? "var(--green-terminal)" : "var(--red-light)",
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
            </span>
            <span
              style={{
                fontSize: 10,
                color: "var(--green-dim)",
                letterSpacing: "0.05em",
              }}
            >
              {agent.onchain_id
                ? `Token ID: ${agent.onchain_id}`
                : "Off-chain"}
              {" · "}
              Registered:{" "}
              {agent.created_at
                ? new Date(agent.created_at).toLocaleDateString()
                : "N/A"}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
          <a
            href={`https://explorer.sepolia.mantle.xyz/address/${agent.wallet_address}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
          >
            View on Explorer
          </a>
          <Link to="/arena" className="btn-secondary">
            Back to Arena
          </Link>
        </div>
      </section>

      {/* Stat Cards */}
      <section style={{ margin: "24px 0" }}>
        <div className="grid-4">
          <div
            className="card"
            style={{
              padding: "20px 16px",
              border: "1.5px solid var(--border-dark)",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "rgba(17,17,17,0.8)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "var(--bg-panel)";
            }}
          >
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 8,
              }}
            >
              Total PnL
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(32px, 4vw, 48px)",
                lineHeight: 1,
                color:
                  totalPnl >= 0 ? "var(--green-terminal)" : "var(--red-light)",
              }}
            >
              {totalPnl >= 0 ? "+" : ""}
              {totalPnl.toFixed(2)}
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--green-dim)",
                marginTop: 6,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {/* TODO: calculate % of starting capital */}
              —
            </div>
          </div>

          <div
            className="card"
            style={{
              padding: "20px 16px",
              border: "1.5px solid var(--border-dark)",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "rgba(17,17,17,0.8)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "var(--bg-panel)";
            }}
          >
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 8,
              }}
            >
              Total Trades
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(32px, 4vw, 48px)",
                lineHeight: 1,
                color: "var(--accent)",
              }}
            >
              {trades.length}
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--green-dim)",
                marginTop: 6,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {winCount}W / {lossCount}L
            </div>
          </div>

          <div
            className="card"
            style={{
              padding: "20px 16px",
              border: "1.5px solid var(--border-dark)",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "rgba(17,17,17,0.8)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "var(--bg-panel)";
            }}
          >
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 8,
              }}
            >
              Win Rate
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(32px, 4vw, 48px)",
                lineHeight: 1,
                color: "var(--accent)",
              }}
            >
              {winRate.toFixed(1)}%
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--green-dim)",
                marginTop: 6,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {winCount} wins / {lossCount} losses
            </div>
          </div>

          <div
            className="card"
            style={{
              padding: "20px 16px",
              border: "1.5px solid var(--border-dark)",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "rgba(17,17,17,0.8)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.background =
                "var(--bg-panel)";
            }}
          >
            <div
              style={{
                fontSize: 9,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "var(--green-dim)",
                marginBottom: 8,
              }}
            >
              Registered
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(32px, 4vw, 48px)",
                lineHeight: 1,
                color: "var(--accent)",
              }}
            >
              {agent.created_at
                ? new Date(agent.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })
                : "N/A"}
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--green-dim)",
                marginTop: 6,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {agent.wallet_address.slice(0, 6)}…
              {agent.wallet_address.slice(-4)}
            </div>
          </div>
        </div>
      </section>

      {/* PnL Chart */}
      <section style={{ marginBottom: 32 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "16px 20px",
            borderBottom: "1.5px solid var(--border-dark)",
            border: "1.5px solid var(--border-dark)",
            borderBottomWidth: "1.5px",
            background: "var(--bg-panel)",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 18,
              color: "var(--surface)",
            }}
          >
            Equity Curve
          </span>
        </div>
        <PnLChart trades={trades} />
      </section>

      {/* Trade History */}
      <section style={{ marginBottom: 48 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "16px 20px",
            borderBottom: "1.5px solid var(--border-dark)",
            border: "2px solid var(--border-dark)",
            background: "var(--bg-panel)",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <span
            style={{
              fontSize: 10,
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              color: "var(--green-dim)",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span style={{ color: "var(--green-terminal)", fontWeight: 700 }}>
              {'>'}
            </span>
            trade_history
          </span>
        </div>

        <div
          style={{
            border: "2px solid var(--border-dark)",
            borderTop: "none",
            background: "var(--bg-panel)",
            overflowX: "auto",
          }}
        >
          {trades.length === 0 ? (
            <div
              style={{
                padding: 48,
                textAlign: "center",
                color: "var(--green-dim)",
                fontSize: 14,
                letterSpacing: "0.08em",
              }}
            >
              No trades executed yet
            </div>
          ) : (
            <>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  minWidth: 700,
                }}
              >
                <thead>
                  <tr>
                    {[
                      "Time",
                      "Pair",
                      "Side",
                      "Price",
                      "Size",
                      "PnL",
                      "Confidence",
                      "Reasoning",
                    ].map((h) => (
                      <th
                        key={h}
                        style={{
                          textAlign: "left",
                          padding: "10px 16px",
                          background: "var(--bg-dark)",
                          borderBottom: "1.5px solid var(--border-dark)",
                          color: "var(--green-terminal)",
                          fontSize: 10,
                          textTransform: "uppercase",
                          letterSpacing: "0.12em",
                          fontWeight: 400,
                          whiteSpace: "nowrap",
                          fontFamily: "var(--font-body)",
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {paginatedTrades.map((t) => (
                    <tr
                      key={t.id}
                      style={{
                        borderBottom: "1px solid rgba(26,58,26,0.5)",
                        transition: "background 0.15s",
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLTableRowElement).style.background =
                          "rgba(51,255,51,0.02)";
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLTableRowElement).style.background =
                          "transparent";
                      }}
                    >
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 11,
                          color: "var(--green-dim)",
                          fontFamily: "var(--font-body)",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.created_at
                          ? new Date(t.created_at).toLocaleTimeString("en-US", {
                              hour12: false,
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })
                          : "—"}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 11,
                          color: "var(--surface)",
                          fontFamily: "var(--font-body)",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.symbol}
                      </td>
                      <td style={{ padding: "10px 16px", whiteSpace: "nowrap" }}>
                        <span
                          style={{
                            fontSize: 10,
                            textTransform: "uppercase",
                            letterSpacing: "0.08em",
                            padding: "2px 8px",
                            border: `1px solid ${t.side.toLowerCase() === "buy" || t.side.toLowerCase() === "long"
                                ? "var(--green-dim)"
                                : "var(--red)"}`,
                            color:
                              t.side.toLowerCase() === "buy" ||
                              t.side.toLowerCase() === "long"
                                ? "var(--green-terminal)"
                                : "var(--red-light)",
                            fontWeight: 700,
                            display: "inline-block",
                          }}
                        >
                          {t.side.toUpperCase()}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 11,
                          color: "var(--surface)",
                          fontFamily: "var(--font-body)",
                          fontVariantNumeric: "tabular-nums",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.price.toFixed(2)}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 11,
                          color: "#aaa",
                          fontFamily: "var(--font-body)",
                          fontVariantNumeric: "tabular-nums",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.quantity.toFixed(4)}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 12,
                          fontWeight: 700,
                          fontFamily: "var(--font-body)",
                          fontVariantNumeric: "tabular-nums",
                          whiteSpace: "nowrap",
                          color:
                            (t.pnl || 0) >= 0
                              ? "var(--green-terminal)"
                              : "var(--red-light)",
                        }}
                      >
                        {t.pnl !== null
                          ? `${t.pnl >= 0 ? "+" : ""}${t.pnl.toFixed(2)}`
                          : "—"}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 11,
                          color: "var(--surface)",
                          fontFamily: "var(--font-body)",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.confidence !== null
                          ? `${(t.confidence * 100).toFixed(0)}%`
                          : "—"}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: 10,
                          color: "#888",
                          fontFamily: "var(--font-body)",
                          maxWidth: 200,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.reasoning ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 20px",
                    borderTop: "1.5px solid var(--border-dark)",
                  }}
                >
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="pg-btn"
                    style={{
                      background: "none",
                      border: "1px solid var(--border-dark)",
                      color: "var(--green-dim)",
                      padding: "6px 12px",
                      fontFamily: "var(--font-body)",
                      fontSize: 10,
                      cursor: page <= 1 ? "default" : "pointer",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      opacity: page <= 1 ? 0.3 : 1,
                    }}
                  >
                    ← Previous
                  </button>
                  <span
                    style={{
                      fontSize: 11,
                      color: "var(--green-dim)",
                      fontFamily: "var(--font-body)",
                    }}
                  >
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="pg-btn"
                    style={{
                      background: "none",
                      border: "1px solid var(--border-dark)",
                      color: "var(--green-dim)",
                      padding: "6px 12px",
                      fontFamily: "var(--font-body)",
                      fontSize: 10,
                      cursor: page >= totalPages ? "default" : "pointer",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      opacity: page >= totalPages ? 0.3 : 1,
                    }}
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
