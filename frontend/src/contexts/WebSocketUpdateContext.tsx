import React, { createContext, useContext, useState, useCallback } from 'react';

interface WebSocketUpdateContextType {
  updateTrigger: number;
  triggerUpdate: () => void;
}

const WebSocketUpdateContext = createContext<WebSocketUpdateContextType | null>(null);

export function useWebSocketUpdate() {
  const context = useContext(WebSocketUpdateContext);
  if (!context) {
    throw new Error('useWebSocketUpdate must be used within a WebSocketUpdateProvider');
  }
  return context;
}

interface WebSocketUpdateProviderProps {
  children: React.ReactNode;
}

export function WebSocketUpdateProvider({ children }: WebSocketUpdateProviderProps) {
  const [updateTrigger, setUpdateTrigger] = useState(0);

  const triggerUpdate = useCallback(() => {
    setUpdateTrigger(prev => prev + 1);
  }, []);

  const value: WebSocketUpdateContextType = {
    updateTrigger,
    triggerUpdate
  };

  return (
    <WebSocketUpdateContext.Provider value={value}>
      {children}
    </WebSocketUpdateContext.Provider>
  );
}
