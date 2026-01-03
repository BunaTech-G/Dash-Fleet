// Simplified API client without authentication
import { SystemStats, FleetEntry, HistoryRow, FleetResponse, HistoryResponse } from '../types';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data?.error || data?.message || message;
    } catch {
      // Keep default message
    }
    throw new Error(message);
  }
  return response.json();
}

/**
 * Get current system stats
 */
export async function fetchStats(): Promise<SystemStats> {
  const response = await fetch('/api/stats');
  return handleResponse<SystemStats>(response);
}

/**
 * Get current status with health score
 */
export async function fetchStatus(): Promise<SystemStats> {
  const response = await fetch('/api/status');
  return handleResponse<SystemStats>(response);
}

/**
 * Get history data
 */
export async function fetchHistory(limit = 300): Promise<HistoryRow[]> {
  const response = await fetch(`/api/history?limit=${limit}`);
  const data = await handleResponse<HistoryResponse>(response);
  return data.data || [];
}

/**
 * Get fleet data
 */
export async function fetchFleet(): Promise<FleetEntry[]> {
  const response = await fetch('/api/fleet');
  const data = await handleResponse<FleetResponse>(response);
  return data.data || [];
}

/**
 * Run system action
 */
export async function runAction(action: string): Promise<any> {
  const response = await fetch('/api/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
  return handleResponse<any>(response);
}
