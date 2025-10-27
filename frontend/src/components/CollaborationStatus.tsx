/**
 * Real-time collaboration status indicator.
 */
import React from 'react';
import { useBoardCollaboration } from '@/contexts/BoardCollaborationContext';

interface CollaborationStatusProps {
  className?: string;
}

export function CollaborationStatus({ className = '' }: CollaborationStatusProps) {
  const { isConnected, boardUpdates } = useBoardCollaboration();

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {/* Connection Status */}
      <div className="flex items-center space-x-1">
        <div 
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className="text-sm text-gray-600">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Recent Updates Counter */}
      {boardUpdates.length > 0 && (
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          <span className="text-sm text-gray-600">
            {boardUpdates.length} recent updates
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * Toast notification for board updates.
 */
interface BoardUpdateToastProps {
  update: {
    id: string;
    type: string;
    data: any;
    timestamp: string;
    userId: string;
  };
  onClose: () => void;
}

export function BoardUpdateToast({ update, onClose }: BoardUpdateToastProps) {
  const getUpdateMessage = () => {
    switch (update.type) {
      case 'board_invitation':
        return 'You have been added to this board!';
      case 'card_moved':
        return 'A card was moved';
      case 'card_updated':
        return 'A card was updated';
      case 'list_updated':
        return 'A list was updated';
      case 'board_updated':
        return 'Board was updated';
      case 'user_typing':
        return 'Someone is typing...';
      default:
        return 'Board updated';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">
            {getUpdateMessage()}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(update.timestamp).toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={onClose}
          className="ml-2 text-gray-400 hover:text-gray-600"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
