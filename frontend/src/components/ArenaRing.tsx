import { motion, AnimatePresence } from "framer-motion";
import type { Score } from "../lib/api";

interface Props {
  scores: Score[];
}

const MEDALS = ["🥇", "🥈", "🥉"];

const PODIUM_COLORS = [
  "var(--amber)",     // gold
  "var(--green-dim)", // silver-ish
  "var(--accent)",    // bronze
];

export default function ArenaRing({ scores }: Props) {
  // Sort by PnL descending for podium ordering
  const sorted = [...scores].sort((a, b) => b.total_pnl - a.total_pnl);
  const maxPnl = Math.max(...sorted.map((s) => Math.abs(s.total_pnl)), 1);

  return (
    <div
      className="card"
      style={{
        padding: "24px 32px",
        border: "1.5px solid var(--border-dark)",
        background: "var(--bg-panel)",
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "18px",
          color: "var(--surface)",
          marginBottom: 24,
          textAlign: "center",
        }}
      >
        Arena Battle
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-end",
          gap: 32,
          minHeight: 280,
          flexWrap: "wrap",
        }}
      >
        <AnimatePresence>
          {sorted.map((s, i) => {
            const height = Math.max(
              (Math.abs(s.total_pnl) / maxPnl) * 200,
              20
            );
            const isPositive = s.total_pnl >= 0;
            const barColor = isPositive
              ? "var(--green-terminal)"
              : "var(--red-light)";
            const borderColor =
              i < 3 ? PODIUM_COLORS[i] : "var(--border-dark)";

            return (
              <motion.div
                key={s.agent_id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                style={{
                  textAlign: "center",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  minWidth: 100,
                }}
              >
                {/* Bar */}
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  style={{
                    width: i === 0 ? 100 : 80,
                    background: barColor,
                    opacity: 0.75,
                    borderTop: i < 3 ? `2px solid ${borderColor}` : "none",
                  }}
                />

                {/* Medal + Info */}
                <div style={{ marginTop: 10 }}>
                  <div
                    style={{
                      fontSize: i === 0 ? "40px" : "32px",
                      lineHeight: 1,
                    }}
                  >
                    {i < 3 ? MEDALS[i] : ""}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "clamp(18px, 2.5vw, 28px)",
                      color: isPositive
                        ? "var(--green-terminal)"
                        : "var(--red-light)",
                      marginTop: 6,
                      lineHeight: 1,
                    }}
                  >
                    {isPositive ? "+" : ""}
                    {s.total_pnl.toFixed(2)}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: 10,
                      color: "var(--green-dim)",
                      marginTop: 4,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                    }}
                  >
                    Agent {s.agent_id.slice(0, 6)}
                  </div>
                  {i < 3 && (
                    <div
                      style={{
                        width: "100%",
                        height: 2,
                        background: borderColor,
                        marginTop: 6,
                      }}
                    />
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
