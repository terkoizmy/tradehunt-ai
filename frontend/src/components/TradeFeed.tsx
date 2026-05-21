import type { Trade } from "../lib/api";

interface Props {
  trades: Trade[];
}

export default function TradeFeed({ trades }: Props) {
  return (
    <div className="card" style={{ maxHeight: "calc(100vh - 120px)", overflow: "hidden", display: "flex", flexDirection: "column" }}>
      <h3 style={{ marginBottom: 12 }}>Live Trade Feed</h3>
      <div style={{ overflowY: "auto", flex: 1 }}>
        {trades.length === 0 ? (
          <p className="muted" style={{ fontSize: 13 }}>
            Waiting for trades...
          </p>
        ) : (
          trades.map((t) => (
            <div
              key={t.id}
              style={{
                padding: "8px 0",
                borderBottom: "1px solid var(--border)",
                fontSize: 12,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span className="muted">{t.symbol}</span>
                <span className={t.side === "buy" ? "positive" : "negative"}>
                  {t.side.toUpperCase()}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                <span>@{t.price.toFixed(2)}</span>
                <span>Qty: {t.quantity.toFixed(4)}</span>
              </div>
              {t.pnl !== null && (
                <div style={{ marginTop: 2 }} className={t.pnl >= 0 ? "positive" : "negative"}>
                  PnL: {t.pnl >= 0 ? "+" : ""}{t.pnl.toFixed(2)} USDT
                </div>
              )}
              {t.reasoning && (
                <div className="muted" style={{ fontSize: 11, marginTop: 2, fontStyle: "italic" }}>
                  "{t.reasoning.slice(0, 80)}{t.reasoning.length > 80 ? "..." : ""}"
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
