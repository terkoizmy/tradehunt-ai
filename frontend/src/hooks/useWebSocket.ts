import { useEffect, useRef, useCallback, useState } from "react";

type ReadyState = "connecting" | "open" | "closed" | "error";

interface WebSocketState<T> {
  data: T | null;
  connected: boolean;
  readyState: ReadyState;
  error: Error | null;
}

export function useWebSocket<T = unknown>(url: string | null): WebSocketState<T> {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [readyState, setReadyState] = useState<ReadyState>("closed");
  const [error, setError] = useState<Error | null>(null);

  const connect = useCallback(() => {
    if (!url) return;

    setReadyState("connecting");
    setError(null);

    try {
      const socket = new WebSocket(url);

      socket.onopen = () => {
        setReadyState("open");
        setError(null);
      };

      socket.onclose = () => {
        setReadyState("closed");
        // Auto-reconnect after 3 seconds
        if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        reconnectTimer.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      socket.onerror = () => {
        setReadyState("error");
        setError(new Error("WebSocket connection failed"));
      };

      socket.onmessage = (event) => {
        try {
          setData(JSON.parse(event.data));
        } catch {
          // Ignore parse errors — data stays as previous valid value
        }
      };

      ws.current = socket;
    } catch (err) {
      setReadyState("error");
      setError(err instanceof Error ? err : new Error(String(err)));
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  return {
    data,
    connected: readyState === "open",
    readyState,
    error,
  };
}
