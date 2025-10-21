/**
 * Board collaboration context for real-time updates.
 */
import React, { createContext, useContext, useCallback, useEffect, useState } from 'react';
import { useBoardWebSocket, WebSocketMessage } from '@/lib/websocket';
import { Board, Card, List } from '@/types';

interface BoardCollaborationContextType {
  isConnected: boolean;
  sendCardMove: (cardId: string, newListId: string, newPosition: number) => void;
  sendCardUpdate: (cardId: string, data: Partial<Card>) => void;
  sendListUpdate: (listId: string, data: Partial<List>) => void;
  sendBoardUpdate: (data: Partial<Board>) => void;
  sendTypingIndicator: (listId: string, isTyping: boolean) => void;
  boardUpdates: BoardUpdate[];
  clearUpdates: () => void;
}

interface BoardUpdate {
  id: string;
  type: string;
  data: any;
  timestamp: string;
  userId: string;
}

const BoardCollaborationContext = createContext<BoardCollaborationContextType | null>(null);

export function useBoardCollaboration() {
  const context = useContext(BoardCollaborationContext);
  if (!context) {
    throw new Error('useBoardCollaboration must be used within a BoardCollaborationProvider');
  }
  return context;
}

interface BoardCollaborationProviderProps {
  children: React.ReactNode;
  boardId: string;
  onBoardUpdate?: (update: BoardUpdate) => void;
}

export function BoardCollaborationProvider({ 
  children, 
  boardId, 
  onBoardUpdate 
}: BoardCollaborationProviderProps) {
  const [boardUpdates, setBoardUpdates] = useState<BoardUpdate[]>([]);
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    const update: BoardUpdate = {
      id: `${message.type}-${Date.now()}-${Math.random()}`,
      type: message.type,
      data: message,
      timestamp: message.timestamp || new Date().toISOString(),
      userId: message.user_id || 'unknown'
    };

    setBoardUpdates(prev => [...prev.slice(-49), update]); // Keep last 50 updates
    onBoardUpdate?.(update);

    // Handle specific message types for real-time updates
    if (message.type === 'card_assigned' || message.type === 'card_unassigned') {
      // These will be handled by the individual components
      console.log('Card assignment update:', message);
    } else if (message.type === 'board_invitation') {
      // Handle board invitation - refresh boards list
      console.log('Board invitation received:', message);
      // This will be handled by the notification system
    } else if (message.type === 'board_state') {
      // Handle initial board state - this should update the board data
      console.log('Board state received:', message);
      // The board state will be handled by the parent component
    } else if (message.type === 'user_notification') {
      // Handle global user notifications
      console.log('User notification received:', message);
      // This will be handled by the notification system
    }
  }, [onBoardUpdate]);

  const { isConnected, sendMessage } = useBoardWebSocket(boardId, {
    onMessage: handleMessage
  });

  const sendCardMove = useCallback((cardId: string, newListId: string, newPosition: number) => {
    sendMessage({
      type: 'card_move',
      card_id: cardId,
      new_list_id: newListId,
      new_position: newPosition
    });
  }, [sendMessage]);

  const sendCardUpdate = useCallback((cardId: string, data: Partial<Card>) => {
    sendMessage({
      type: 'card_update',
      card_id: cardId,
      data
    });
  }, [sendMessage]);

  const sendListUpdate = useCallback((listId: string, data: Partial<List>) => {
    sendMessage({
      type: 'list_update',
      list_id: listId,
      data
    });
  }, [sendMessage]);

  const sendBoardUpdate = useCallback((data: Partial<Board>) => {
    sendMessage({
      type: 'board_update',
      data
    });
  }, [sendMessage]);

  const sendTypingIndicator = useCallback((listId: string, isTyping: boolean) => {
    sendMessage({
      type: 'user_typing',
      data: {
        list_id: listId,
        is_typing: isTyping
      },
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  const clearUpdates = useCallback(() => {
    setBoardUpdates([]);
  }, []);

  const value: BoardCollaborationContextType = {
    isConnected,
    sendCardMove,
    sendCardUpdate,
    sendListUpdate,
    sendBoardUpdate,
    sendTypingIndicator,
    boardUpdates,
    clearUpdates
  };

  return (
    <BoardCollaborationContext.Provider value={value}>
      {children}
    </BoardCollaborationContext.Provider>
  );
}
