import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";
import type { Trade } from "../lib/api";

interface Props {
  trades: Trade[];
}

export default function PnLChart({ trades }: Props) {
  const STARTING_CAPITAL = 10000;

  let running = 0;
  const data = trades
    .slice()
    .sort((a, b) =>
      new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
    )
    .map((t) => {
      running += t.pnl || 0;
      return {
        time: t.created_at
          ? new Date(t.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })
          : "",
        pnl: running,
        equity: STARTING_CAPITAL + running,
      };
    });

  if (data.length === 0) {
    return (
      <div
        style={{
          height: 320,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#080808",
          border: "1.5px solid var(--border-dark)",
        }}
      >
        <span style={{ color: "var(--green-dim)", fontSize: 12 }}>
          No trade data to chart
        </span>
      </div>
    );
  }

  const latestPnl = data[data.length - 1]?.pnl ?? 0;
  const lineColor = latestPnl >= 0 ? "#33ff33" : "#C44545";

  return (
    <div
      style={{
        border: "1.5px solid var(--border-dark)",
        background: "#080808",
      }}
    >
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid
            stroke="rgba(26,58,26,0.3)"
            strokeWidth={0.5}
            vertical={false}
          />
          <XAxis
            dataKey="time"
            stroke="#1a8a1a"
            fontSize={10}
            tickLine={false}
            axisLine={{ stroke: "rgba(26,58,26,0.3)" }}
            tick={{ fontFamily: "var(--font-body)", fill: "#1a8a1a" }}
          />
          <YAxis
            stroke="#1a8a1a"
            fontSize={10}
            tickLine={false}
            axisLine={{ stroke: "rgba(26,58,26,0.3)" }}
            tick={{ fontFamily: "var(--font-body)", fill: "#1a8a1a" }}
            tickFormatter={(v: number) => v.toFixed(0)}
          />
          <ReferenceLine
            y={0}
            stroke="rgba(26,58,26,0.5)"
            strokeDasharray="6 4"
          />
          <Tooltip
            contentStyle={{
              background: "#111111",
              border: "1px solid var(--border-dark)",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              color: "var(--green-terminal)",
            }}
            labelStyle={{
              color: "var(--green-dim)",
              fontFamily: "var(--font-mono)",
              fontSize: 10,
            }}
            itemStyle={{
              color: "var(--green-terminal)",
              fontFamily: "var(--font-mono)",
            }}
            formatter={(value: number) => [
              `${value >= 0 ? "+" : ""}${value.toFixed(2)} USDT`,
              "PnL",
            ]}
          />
          <Line
            type="monotone"
            dataKey="pnl"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              fill: lineColor,
              stroke: "var(--bg-dark)",
              strokeWidth: 2,
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
