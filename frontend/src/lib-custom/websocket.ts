/**
 * WebSocket client for real-time board collaboration.
 */

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface WebSocketClientOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onOpen?: (event: Event) => void;
}

export class BoardWebSocketClient {
  private ws: WebSocket | null = null;
  private boardId: string;
  private token: string;
  private options: WebSocketClientOptions;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  constructor(boardId: string, options: WebSocketClientOptions = {}) {
    this.boardId = boardId;
    this.token = localStorage.getItem('access_token') || '';
    this.options = options;
  }

  connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return Promise.resolve();
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.buildWebSocketUrl();
        console.log('Connecting to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = (event) => {
          console.log('WebSocket connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.options.onOpen?.(event);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log('WebSocket message received:', message);
            this.options.onMessage?.(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          this.options.onError?.(error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.isConnecting = false;
          this.options.onClose?.(event);
          
          // Attempt to reconnect if not a normal closure and not authentication errors
          if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message);
    }
  }

  private buildWebSocketUrl(): string {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = baseUrl.replace('http', 'ws');
    return `${wsUrl}/ws/board/${this.boardId}?token=${this.token}`;
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect().catch(() => {
        // Reconnection failed, will be handled by onclose
      });
    }, delay);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Hook for using WebSocket in React components
export function useBoardWebSocket(boardId: string, options: WebSocketClientOptions = {}) {
  const [client, setClient] = useState<BoardWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!boardId) return;

    const wsClient = new BoardWebSocketClient(boardId, {
      ...options,
      onOpen: (event) => {
        setIsConnected(true);
        options.onOpen?.(event);
      },
      onClose: (event) => {
        setIsConnected(false);
        options.onClose?.(event);
      },
      onError: (error) => {
        setIsConnected(false);
        options.onError?.(error);
      }
    });

    setClient(wsClient);

    // Connect when component mounts
    wsClient.connect().catch(console.error);

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, [boardId]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    client?.send(message);
  }, [client]);

  return {
    client,
    isConnected,
    sendMessage
  };
}

// Import React hooks
import { useState, useEffect, useCallback } from 'react';
