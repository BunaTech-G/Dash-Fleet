// Hook for fetching history data
import { useQuery } from '@tanstack/react-query';
import { fetchHistory } from '../services/api';
import { HistoryRow } from '../types';

export function useHistory(limit = 300) {
  return useQuery<HistoryRow[], Error>({
    queryKey: ['history', limit],
    queryFn: () => fetchHistory(limit),
    refetchInterval: 5000,
  });
}
