import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import type { Score } from "../lib/api";

interface Props {
  scores: Score[];
}

type SortKey = "rank" | "total_pnl" | "sharpe_ratio" | "win_rate" | "trade_count";
type SortDir = "asc" | "desc";

const MEDALS = ["🥇", "🥈", "🥉"];
const PODIUM_BORDERS = [
  "var(--amber)",
  "var(--green-dim)",
  "var(--accent)",
];

export default function LeaderboardTable({ scores }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("rank");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "total_pnl" || key === "sharpe_ratio" || key === "win_rate" ? "desc" : "asc");
    }
  };

  const sorted = useMemo(() => {
    const data = [...scores];
    data.sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];
      if (av === null || av === undefined) av = sortDir === "asc" ? Infinity : -Infinity;
      if (bv === null || bv === undefined) bv = sortDir === "asc" ? Infinity : -Infinity;
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return data;
  }, [scores, sortKey, sortDir]);

  const headerCell = (key: SortKey, label: string) => {
    const active = sortKey === key;
    return (
      <th
        onClick={() => handleSort(key)}
        style={{
          cursor: "pointer",
          userSelect: "none",
          color: active ? "var(--green-terminal)" : "var(--green-terminal)",
          whiteSpace: "nowrap",
        }}
      >
        {label}
        {active && (
          <span style={{ marginLeft: 4 }}>{sortDir === "asc" ? "▲" : "▼"}</span>
        )}
      </th>
    );
  };

  return (
    <div
      style={{
        border: "2px solid var(--border-dark)",
        background: "var(--bg-panel)",
        overflowX: "auto",
      }}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          minWidth: 640,
        }}
      >
        <thead>
          <tr>
            <th
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
              }}
            >
              Rank
            </th>
            {headerCell("total_pnl", "PnL")}
            {headerCell("sharpe_ratio", "Sharpe")}
            {headerCell("win_rate", "Win Rate")}
            {headerCell("trade_count", "Trades")}
            <th
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
              }}
            >
              Agent
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => {
            const isTop3 = s.rank <= 3;
            const borderLeft = isTop3
              ? `3px solid ${PODIUM_BORDERS[s.rank - 1]}`
              : "none";

            return (
              <tr
                key={s.agent_id}
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
                    fontVariantNumeric: "tabular-nums",
                    fontSize: 12,
                    borderLeft,
                  }}
                >
                  <span style={{ fontSize: 14 }}>
                    {isTop3 ? MEDALS[s.rank - 1] : s.rank}
                  </span>
                </td>
                <td
                  style={{
                    padding: "10px 16px",
                    fontVariantNumeric: "tabular-nums",
                    fontSize: 11,
                    color:
                      s.total_pnl >= 0
                        ? "var(--green-terminal)"
                        : "var(--red-light)",
                    fontWeight: 600,
                  }}
                >
                  {s.total_pnl >= 0 ? "+" : ""}
                  {s.total_pnl.toFixed(2)} USDT
                </td>
                <td
                  style={{
                    padding: "10px 16px",
                    fontVariantNumeric: "tabular-nums",
                    fontSize: 11,
                    color: "var(--surface)",
                  }}
                >
                  {s.sharpe_ratio?.toFixed(2) ?? "—"}
                </td>
                <td
                  style={{
                    padding: "10px 16px",
                    fontVariantNumeric: "tabular-nums",
                    fontSize: 11,
                    color: "var(--surface)",
                  }}
                >
                  {s.win_rate !== null
                    ? `${(s.win_rate * 100).toFixed(1)}%`
                    : "—"}
                </td>
                <td
                  style={{
                    padding: "10px 16px",
                    fontVariantNumeric: "tabular-nums",
                    fontSize: 11,
                    color: "var(--surface)",
                  }}
                >
                  {s.trade_count}
                </td>
                <td
                  style={{
                    padding: "10px 16px",
                    fontSize: 11,
                  }}
                >
                  <Link
                    to={`/agents/${s.agent_id}`}
                    style={{
                      color: "var(--green-terminal)",
                      textDecoration: "none",
                      fontFamily: "var(--font-body)",
                    }}
                  >
                    {s.agent_id.slice(0, 8)}…
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
