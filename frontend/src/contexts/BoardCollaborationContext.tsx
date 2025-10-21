/**
 * Board collaboration context for real-time updates.
 */
import React, { createContext, useContext, useCallback, useEffect, useState } from 'react';
import { useBoardWebSocket, WebSocketMessage } from '@/lib-custom/websocket';
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
    console.log('Board collaboration message received:', message);
    
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
    switch (message.type) {
      case 'connection':
        console.log('WebSocket connection established:', message);
        break;
      case 'board_state':
        console.log('Board state received:', message);
        // The board state will be handled by the parent component
        break;
      case 'card_moved':
      case 'card_updated':
      case 'card_assigned':
      case 'card_unassigned':
        console.log('Card update received:', message);
        // These will be handled by the individual components
        break;
      case 'card_created':
        console.log('Card created:', message);
        // Trigger board data refresh
        break;
      case 'card_deleted':
        console.log('Card deleted:', message);
        // Trigger board data refresh
        break;
      case 'list_updated':
        console.log('List update received:', message);
        break;
      case 'list_created':
        console.log('List created:', message);
        // Trigger board data refresh
        break;
      case 'list_deleted':
        console.log('List deleted:', message);
        // Trigger board data refresh
        break;
      case 'board_updated':
        console.log('Board update received:', message);
        break;
      case 'board_deleted':
        console.log('Board deleted:', message);
        // Redirect to dashboard
        if (message.redirect) {
          window.location.href = '/';
        }
        break;
      case 'user_typing':
        console.log('User typing indicator:', message);
        break;
      case 'board_invitation':
        console.log('Board invitation received:', message);
        // This will be handled by the notification system
        break;
      case 'user_notification':
        console.log('User notification received:', message);
        // This will be handled by the notification system
        break;
      case 'error':
        console.error('WebSocket error message:', message);
        break;
      default:
        console.log('Unknown message type:', message.type, message);
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
