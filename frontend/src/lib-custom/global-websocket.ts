/**
 * Global WebSocket client for user notifications.
 */

export interface GlobalWebSocketMessage {
  type: string;
  user_id?: string;
  notification?: any;
  [key: string]: any;
}

export interface GlobalWebSocketClientOptions {
  onMessage?: (message: GlobalWebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onOpen?: (event: Event) => void;
}

export class GlobalWebSocketClient {
  private ws: WebSocket | null = null;
  private token: string;
  private options: GlobalWebSocketClientOptions;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  constructor(options: GlobalWebSocketClientOptions = {}) {
    this.token = localStorage.getItem('access_token') || '';
    this.options = options;
  }

  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected()) {
      return;
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        const url = this.buildWebSocketUrl();
        console.log('Connecting to global WebSocket:', url);
        
        this.ws = new WebSocket(url);

        this.ws.onopen = (event) => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.options.onOpen?.(event);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.options.onMessage?.(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          this.isConnecting = false;
          this.options.onError?.(error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('Global WebSocket closed:', event.code, event.reason);
          this.isConnecting = false;
          this.options.onClose?.(event);
          
          // Attempt to reconnect if not a normal closure and not authentication errors
          if (event.code !== 1000 && event.code !== 4001 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

      } catch (error) {
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

  send(message: GlobalWebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('Global WebSocket is not connected. Cannot send message:', message);
    }
  }

  private buildWebSocketUrl(): string {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = baseUrl.replace('http', 'ws');
    return `${wsUrl}/ws/notifications?token=${this.token}`;
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Attempting to reconnect global WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect().catch(() => {
        // Reconnection failed, will be handled by onclose
      });
    }, delay);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
