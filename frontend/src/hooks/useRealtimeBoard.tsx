import { useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { boardsApi } from '@/services/boards';
import { useBoardCollaboration } from '@/contexts/BoardCollaborationContext';
import { useWebSocketUpdate } from '@/contexts/WebSocketUpdateContext';

/**
 * Custom hook for real-time board data with automatic WebSocket updates
 */
export function useRealtimeBoard(boardId: string) {
  const queryClient = useQueryClient();
  const { forceUpdate } = useBoardCollaboration();
  const { updateTrigger } = useWebSocketUpdate();
  const lastUpdateRef = useRef(0);

  // Fetch board data
  const boardQuery = useQuery({
    queryKey: ['board', boardId],
    queryFn: () => boardsApi.getBoard(boardId),
    enabled: !!boardId,
    staleTime: 0, // Always consider data stale to ensure fresh updates
    refetchOnWindowFocus: false,
  });

  // Force refetch when WebSocket updates are received
  useEffect(() => {
    const currentUpdate = forceUpdate + updateTrigger;
    if (currentUpdate > lastUpdateRef.current) {
      lastUpdateRef.current = currentUpdate;
      console.log('WebSocket update detected, refetching board data', { 
        forceUpdate, 
        updateTrigger, 
        boardId 
      });
      boardQuery.refetch();
    }
  }, [forceUpdate, updateTrigger, boardId, boardQuery]);

  // Invalidate and refetch when board data changes
  const invalidateBoard = () => {
    queryClient.invalidateQueries({ queryKey: ['board', boardId] });
    queryClient.invalidateQueries({ queryKey: ['boards'] });
    boardQuery.refetch();
  };

  return {
    board: boardQuery.data,
    isLoading: boardQuery.isLoading,
    error: boardQuery.error,
    refetch: boardQuery.refetch,
    invalidateBoard,
    isConnected: true, // This would come from WebSocket context
  };
}
