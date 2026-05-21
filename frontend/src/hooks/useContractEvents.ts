import { useWatchContractEvent } from "wagmi";
import { CONTRACTS } from "../lib/contracts";
import { useState } from "react";

// ABI fragments for events we care about
const tradeExecutedAbi = {
  event: {
    name: "TradeExecuted",
    type: "event",
    inputs: [
      { indexed: true, name: "agentId", type: "uint256" },
      { name: "symbol", type: "string" },
      { name: "side", type: "string" },
      { name: "price", type: "uint256" },
      { name: "quantity", type: "uint256" },
      { name: "pnl", type: "int256" },
      { name: "timestamp", type: "uint256" },
    ],
  },
} as const;

export interface TradeEvent {
  agentId: bigint;
  symbol: string;
  side: string;
  price: bigint;
  quantity: bigint;
  pnl: bigint;
  timestamp: bigint;
}

export function useTradeEvents() {
  const [events, setEvents] = useState<TradeEvent[]>([]);

  useWatchContractEvent({
    address: CONTRACTS.tradeRegistry as `0x${string}`,
    abi: [tradeExecutedAbi],
    eventName: "TradeExecuted",
    onLogs(logs) {
      for (const log of logs) {
        const args = (log as unknown as { args: TradeEvent }).args;
        if (args) {
          setEvents((prev) => [...prev.slice(-99), args]);
        }
      }
    },
  });

  return events;
}
