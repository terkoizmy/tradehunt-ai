const API_BASE = "http://localhost:8000";

export interface Agent {
  id: string;
  name: string;
  persona: string;
  wallet_address: string;
  status: string;
  onchain_id: number | null;
  created_at: string;
}

export interface Session {
  id: string;
  name: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  onchain_id: number | null;
}

export interface Trade {
  id: string;
  agent_id: string;
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  pnl: number | null;
  confidence: number | null;
  reasoning: string | null;
  tx_hash: string | null;
  created_at: string | null;
}

export interface Score {
  rank: number;
  agent_id: string;
  total_pnl: number;
  sharpe_ratio: number | null;
  win_rate: number | null;
  trade_count: number;
}

export async function fetchAgents(persona?: string): Promise<Agent[]> {
  const params = persona ? `?persona=${persona}` : "";
  const res = await fetch(`${API_BASE}/api/agents${params}`);
  return res.json();
}

export async function fetchAgent(id: string): Promise<Agent> {
  const res = await fetch(`${API_BASE}/api/agents/${id}`);
  return res.json();
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/api/arena/sessions`);
  return res.json();
}

export async function fetchSession(id: string): Promise<{
  id: string;
  name: string;
  status: string;
  scores: Score[];
}> {
  const res = await fetch(`${API_BASE}/api/arena/sessions/${id}`);
  return res.json();
}

export async function fetchTrades(
  agentId?: string,
  symbol?: string,
  limit = 50
): Promise<Trade[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (agentId) params.set("agent_id", agentId);
  if (symbol) params.set("symbol", symbol);
  const res = await fetch(`${API_BASE}/api/trades?${params}`);
  return res.json();
}

export async function fetchLeaderboard(sessionId: string): Promise<Score[]> {
  const res = await fetch(`${API_BASE}/api/leaderboard/${sessionId}`);
  return res.json();
}
