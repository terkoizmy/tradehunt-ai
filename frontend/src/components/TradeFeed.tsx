import { useEffect, useRef } from "react";
import type { Trade } from "../lib/api";

interface Props {
  trades: Trade[];
  connected?: boolean;
}

function formatTime(iso: string | null): string {
  if (!iso) return "--:--";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function TradeFeed({ trades, connected = false }: Props) {
  const listRef = useRef<HTMLDivElement>(null);

  const visibleTrades = trades.slice(0, 100);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [trades.length]);

  return (
    <div className="tf-panel" style={{ maxHeight: "calc(100vh - 120px)" }}>
      <div className="tf-header">
        <span className="tf-title">trade_feed</span>
        <span className={`tf-status ${connected ? "connected" : ""}`}>
          {connected ? "LIVE" : "OFFLINE"}
        </span>
      </div>
      <div ref={listRef} className="tf-list">
        {visibleTrades.length === 0 ? (
          <div className="tf-empty">
            <div className="tf-empty-prompt">$ _</div>
            <div>Waiting for agent signals...</div>
          </div>
        ) : (
          visibleTrades.map((t) => {
            const isBuy = t.side.toLowerCase() === "buy";
            const pnl = t.pnl ?? 0;
            const pnlPositive = pnl >= 0;

            return (
              <div key={t.id} className="tf-item">
                <div className="tf-row">
                  <div className={`tf-dot ${isBuy ? "buy" : "sell"}`} />
                  <span className="tf-time">{formatTime(t.created_at)}</span>
                  <span className="tf-symbol">{t.symbol}</span>
                  <span className={`tf-badge ${isBuy ? "buy" : "sell"}`}>
                    {t.side.toUpperCase()}
                  </span>
                  <span className={`tf-pnl ${pnlPositive ? "up" : "down"}`}>
                    {pnlPositive ? "+" : ""}
                    {pnl.toFixed(2)}
                  </span>
                </div>
                <div className="tf-row tf-detail">
                  <span>@{t.price.toFixed(2)}</span>
                  <span>Qty: {t.quantity.toFixed(4)}</span>
                  {t.confidence !== null && (
                    <span>Conf: {(t.confidence * 100).toFixed(0)}%</span>
                  )}
                </div>
                {t.reasoning && (
                  <div className="tf-reasoning">
                    &ldquo;{t.reasoning.length > 60
                      ? `${t.reasoning.slice(0, 60)}...`
                      : t.reasoning}&rdquo;
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
