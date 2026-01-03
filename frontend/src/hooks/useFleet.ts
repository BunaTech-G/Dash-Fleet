// Hook for fetching fleet data
import { useQuery } from '@tanstack/react-query';
import { fetchFleet } from '../services/api';
import { FleetEntry } from '../types';

const TTL_SECONDS = parseInt(import.meta.env.VITE_FLEET_TTL || '600', 10);

export function useFleet() {
  return useQuery<FleetEntry[], Error>({
    queryKey: ['fleet'],
    queryFn: fetchFleet,
    refetchInterval: 5000,
  });
}

export function getEntryStatus(entry: FleetEntry): 'ok' | 'warn' | 'critical' | 'expired' {
  const now = Date.now() / 1000;
  if (now - entry.ts > TTL_SECONDS) return 'expired';
  const status = (entry.report as any)?.health?.status || 'ok';
  return status;
}

export function getEntryScore(entry: FleetEntry): number {
  return (entry.report as any)?.health?.score ?? 0;
}
