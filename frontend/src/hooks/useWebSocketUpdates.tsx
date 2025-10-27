import { useCallback, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Hook to handle WebSocket updates and force component re-renders
 */
export function useWebSocketUpdates(boardId: string) {
  const queryClient = useQueryClient();
  const [updateTrigger, setUpdateTrigger] = useState(0);

  const triggerUpdate = useCallback(() => {
    setUpdateTrigger(prev => prev + 1);
  }, []);

  const handleWebSocketUpdate = useCallback((message: any) => {
    console.log('WebSocket update received:', message);
    
    // Force a re-render by updating the trigger
    triggerUpdate();
    
    // Invalidate and refetch queries
    queryClient.invalidateQueries({ queryKey: ['board', boardId] });
    queryClient.invalidateQueries({ queryKey: ['boards'] });
    queryClient.refetchQueries({ queryKey: ['board', boardId] });
  }, [boardId, queryClient, triggerUpdate]);

  return {
    updateTrigger,
    handleWebSocketUpdate,
    triggerUpdate
  };
}
