import { useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { boardsApi } from '@/services/boards';
import { useWebSocketUpdate } from '@/contexts/WebSocketUpdateContext';

/**
 * Custom hook for real-time boards list with automatic WebSocket updates
 */
export function useRealtimeBoards() {
  const queryClient = useQueryClient();
  const { updateTrigger } = useWebSocketUpdate();
  const lastUpdateRef = useRef(0);

  // Fetch boards data
  const boardsQuery = useQuery({
    queryKey: ['boards'],
    queryFn: boardsApi.getBoards,
    staleTime: 0, // Always consider data stale to ensure fresh updates
    refetchOnWindowFocus: false,
  });

  // Force refetch when WebSocket updates are received
  useEffect(() => {
    if (updateTrigger > lastUpdateRef.current) {
      lastUpdateRef.current = updateTrigger;
      console.log('WebSocket update detected, refetching boards data', { updateTrigger });
      boardsQuery.refetch();
    }
  }, [updateTrigger, boardsQuery]);

  // Invalidate and refetch when boards data changes
  const invalidateBoards = () => {
    queryClient.invalidateQueries({ queryKey: ['boards'] });
    boardsQuery.refetch();
  };

  return {
    boards: boardsQuery.data || [],
    isLoading: boardsQuery.isLoading,
    error: boardsQuery.error,
    refetch: boardsQuery.refetch,
    invalidateBoards,
  };
}
