// Hook for fetching system stats
import { useQuery } from '@tanstack/react-query';
import { fetchStatus } from '../services/api';
import { SystemStats } from '../types';

export function useStats() {
  return useQuery<SystemStats, Error>({
    queryKey: ['stats'],
    queryFn: fetchStatus,
    refetchInterval: 2500,
  });
}
