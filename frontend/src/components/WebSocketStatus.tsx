import React from 'react';
import { useBoardCollaboration } from '@/contexts/BoardCollaborationContext';

interface WebSocketStatusProps {
  className?: string;
}

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({ className = '' }) => {
  const { isConnected } = useBoardCollaboration();

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <span className="text-xs text-gray-500">
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
};
