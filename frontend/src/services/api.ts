export type HealthStatus = 'ok' | 'warn' | 'critical';

export interface Health {
  score: number;
  status: HealthStatus;
  components?: { cpu: number; ram: number; disk: number };
}

export interface StatusPayload {
  timestamp: string;
  cpu_percent: number;
  ram_percent: number;
  ram_used_gib: number;
  ram_total_gib: number;
  disk_percent: number;
  disk_used_gib: number;
  disk_total_gib: number;
  uptime_seconds: number;
  uptime_hms: string;
  alerts: { cpu: boolean; ram: boolean };
  alert_active: boolean;
  health: Health;
}

export interface HistoryRow {
  timestamp: string;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  uptime_hms?: string;
}

export interface FleetEntry {
  id: string;
  ts: number;
  client?: string;
  org_id?: string;
  report: StatusPayload | Record<string, any>;
}

function buildHeaders(apiKey?: string | null): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
  return headers;
}

async function handle<T>(resp: Response): Promise<T> {
  const data = await resp.json();
  if (!resp.ok) {
    const message = data?.error || data?.message || `HTTP ${resp.status}`;
    throw new Error(message);
  }
  return data as T;
}

export async function fetchStatus(apiKey?: string | null): Promise<StatusPayload> {
  const resp = await fetch('/api/status', { headers: buildHeaders(apiKey) });
  return handle<StatusPayload>(resp);
}

export async function fetchHistory(limit = 300, apiKey?: string | null): Promise<HistoryRow[]> {
  const resp = await fetch(`/api/history?limit=${limit}`, { headers: buildHeaders(apiKey) });
  const data = await handle<{ data: HistoryRow[] }>(resp);
  return data.data || [];
}

export async function fetchFleet(apiKey?: string | null): Promise<FleetEntry[]> {
  const resp = await fetch('/api/fleet', { headers: buildHeaders(apiKey) });
  const data = await handle<{ data: FleetEntry[] }>(resp);
  return data.data || [];
}

export async function runAction(action: string, apiKey?: string | null) {
  const resp = await fetch('/api/action', {
    method: 'POST',
    headers: buildHeaders(apiKey),
    body: JSON.stringify({ action }),
  });
  return handle(resp);
}

export async function fetchTokens(actionToken: string, apiKey?: string | null) {
  const headers = buildHeaders(apiKey);
  headers['Authorization'] = `Bearer ${actionToken}`;
  const resp = await fetch('/api/tokens', { headers });
  return handle<{ items: any[]; count: number }>(resp);
}

export async function createToken(payload: { path: string; ttl: number }, actionToken: string, apiKey?: string | null) {
  const headers = buildHeaders(apiKey);
  headers['Authorization'] = `Bearer ${actionToken}`;
  const resp = await fetch('/api/tokens/create', { method: 'POST', headers, body: JSON.stringify(payload) });
  return handle<{ link: string; expires_in: number }>(resp);
}

export async function deleteToken(token: string, actionToken: string, apiKey?: string | null) {
  const headers = buildHeaders(apiKey);
  headers['Authorization'] = `Bearer ${actionToken}`;
  const resp = await fetch('/api/tokens/delete', { method: 'POST', headers, body: JSON.stringify({ token }) });
  return handle<{ ok: boolean }>(resp);
}
