import { useWatchContractEvent } from "wagmi";
import { CONTRACTS } from "../lib/contracts";
import { useState, useCallback } from "react";

// Standard Solidity JSON ABI for TradeRegistry events
const tradeRegistryAbi = [
  {
    type: "event",
    name: "TradeExecuted",
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
  {
    type: "event",
    name: "AgentLinked",
    inputs: [
      { indexed: true, name: "agentId", type: "uint256" },
      { indexed: true, name: "wallet", type: "address" },
    ],
  },
] as const;

export interface TradeEvent {
  agentId: bigint;
  symbol: string;
  side: string;
  price: bigint;
  quantity: bigint;
  pnl: bigint;
  timestamp: bigint;
  blockNumber?: bigint;
  transactionHash?: string;
  logIndex?: number;
}

const MAX_EVENTS = 100;

export function useTradeEvents() {
  const [events, setEvents] = useState<TradeEvent[]>([]);

  const handleLogs = useCallback((logs: unknown[]) => {
    for (const log of logs) {
      const l = log as {
        args?: {
          agentId?: bigint;
          symbol?: string;
          side?: string;
          price?: bigint;
          quantity?: bigint;
          pnl?: bigint;
          timestamp?: bigint;
        };
        blockNumber?: bigint;
        transactionHash?: string;
        logIndex?: number;
      };

      const args = l.args;
      if (
        args &&
        args.agentId !== undefined &&
        args.symbol !== undefined &&
        args.side !== undefined &&
        args.price !== undefined &&
        args.quantity !== undefined &&
        args.pnl !== undefined &&
        args.timestamp !== undefined
      ) {
        const evt: TradeEvent = {
          agentId: args.agentId,
          symbol: args.symbol,
          side: args.side,
          price: args.price,
          quantity: args.quantity,
          pnl: args.pnl,
          timestamp: args.timestamp,
          blockNumber: l.blockNumber,
          transactionHash: l.transactionHash,
          logIndex: l.logIndex,
        };

        setEvents((prev) => {
          // Prevent duplicates by transactionHash + logIndex
          const key = `${evt.transactionHash ?? ""}-${evt.logIndex ?? ""}`;
          const exists = prev.some(
            (p) =>
              `${p.transactionHash ?? ""}-${p.logIndex ?? ""}` === key
          );
          if (exists) return prev;
          return [evt, ...prev].slice(0, MAX_EVENTS);
        });
      }
    }
  }, []);

  useWatchContractEvent({
    address:
      CONTRACTS.tradeRegistry !== "0x0000000000000000000000000000000000000000"
        ? (CONTRACTS.tradeRegistry as `0x${string}`)
        : undefined,
    abi: tradeRegistryAbi,
    eventName: "TradeExecuted",
    onLogs: handleLogs,
  });

  return events;
}

export function useAgentLinkedEvents() {
  const [events, setEvents] = useState<
    { agentId: bigint; wallet: string }[]
  >([]);

  useWatchContractEvent({
    address:
      CONTRACTS.tradeRegistry !== "0x0000000000000000000000000000000000000000"
        ? (CONTRACTS.tradeRegistry as `0x${string}`)
        : undefined,
    abi: tradeRegistryAbi,
    eventName: "AgentLinked",
    onLogs(logs) {
      for (const log of logs) {
        const l = log as {
          args?: { agentId?: bigint; wallet?: string };
        };
        if (l.args?.agentId !== undefined && l.args.wallet) {
          setEvents((prev) =>
            [...prev, { agentId: l.args!.agentId!, wallet: l.args!.wallet! }].slice(
              -MAX_EVENTS
            )
          );
        }
      }
    },
  });

  return events;
}
