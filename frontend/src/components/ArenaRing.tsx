import { motion } from "framer-motion";
import type { Score } from "../lib/api";

interface Props {
  scores: Score[];
}

export default function ArenaRing({ scores }: Props) {
  const maxPnl = Math.max(...scores.map((s) => Math.abs(s.total_pnl)), 1);

  return (
    <div className="card" style={{ padding: 32 }}>
      <h3 style={{ marginBottom: 24, textAlign: "center" }}>Arena Battle</h3>
      <div style={{ display: "flex", justifyContent: "center", gap: 32, alignItems: "flex-end" }}>
        {scores.map((s, i) => {
          const height = (Math.abs(s.total_pnl) / maxPnl) * 200;
          const isPositive = s.total_pnl >= 0;
          return (
            <div key={s.agent_id} style={{ textAlign: "center" }}>
              <motion.div
                initial={{ height: 0 }}
                animate={{ height }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                style={{
                  width: 80,
                  background: isPositive ? "var(--accent-green)" : "var(--accent-red)",
                  borderRadius: "4px 4px 0 0",
                  opacity: 0.8,
                }}
              />
              <div style={{ marginTop: 8 }}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 13 }}>
                  {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : ""}
                </div>
                <div className={`stat-value ${isPositive ? "positive" : "negative"}`} style={{ fontSize: 16 }}>
                  {isPositive ? "+" : ""}{s.total_pnl.toFixed(1)}
                </div>
                <div className="stat-label" style={{ fontSize: 10 }}>
                  Agent {s.agent_id.slice(0, 6)}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
