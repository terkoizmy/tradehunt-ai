import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { Trade } from "../lib/api";

interface Props {
  trades: Trade[];
}

export default function PnLChart({ trades }: Props) {
  let running = 0;
  const data = trades
    .slice()
    .reverse()
    .map((t) => {
      running += t.pnl || 0;
      return {
        time: t.created_at ? new Date(t.created_at).toLocaleTimeString() : "",
        pnl: running,
      };
    });

  if (data.length === 0) {
    return (
      <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="muted">No trade data to chart</span>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis
          dataKey="time"
          stroke="var(--text-muted)"
          fontSize={10}
          tickLine={false}
        />
        <YAxis
          stroke="var(--text-muted)"
          fontSize={10}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        />
        <Line
          type="monotone"
          dataKey="pnl"
          stroke="var(--accent-green)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
