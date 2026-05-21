import { useEffect, useRef, useCallback, useState } from "react";

export function useWebSocket<T = unknown>(url: string | null) {
  const ws = useRef<WebSocket | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    if (!url) return;
    const socket = new WebSocket(url);
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      try {
        setData(JSON.parse(event.data));
      } catch {
        // ignore parse errors
      }
    };
    ws.current = socket;
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  return { data, connected };
}
