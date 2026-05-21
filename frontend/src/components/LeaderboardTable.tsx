import type { Score } from "../lib/api";

interface Props {
  scores: Score[];
}

export default function LeaderboardTable({ scores }: Props) {
  return (
    <div className="card" style={{ overflowX: "auto" }}>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Agent ID</th>
            <th>Total PnL</th>
            <th>Sharpe</th>
            <th>Win Rate</th>
            <th>Trades</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((s) => (
            <tr key={s.agent_id}>
              <td>
                {s.rank === 1 ? "🥇" : s.rank === 2 ? "🥈" : s.rank === 3 ? "🥉" : `#${s.rank}`}
              </td>
              <td>
                <code style={{ fontSize: 12 }}>
                  {s.agent_id.slice(0, 8)}...
                </code>
              </td>
              <td className={s.total_pnl >= 0 ? "positive" : "negative"}>
                {s.total_pnl >= 0 ? "+" : ""}
                {s.total_pnl.toFixed(2)} USDT
              </td>
              <td>{s.sharpe_ratio?.toFixed(2) || "-"}</td>
              <td>{s.win_rate !== null ? `${(s.win_rate * 100).toFixed(1)}%` : "-"}</td>
              <td>{s.trade_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
