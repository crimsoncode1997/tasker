"""
Redis connection and pub/sub management.
"""
import asyncio
import json
from typing import Dict, Set, Any
import redis.asyncio as redis
import structlog
from fastapi import WebSocket

from app.core.config import settings

logger = structlog.get_logger()


def is_websocket_connected(websocket: WebSocket) -> bool:
    """Check if WebSocket connection is still active."""
    try:
        # Check if WebSocket has client_state attribute and is not disconnected
        if hasattr(websocket, 'client_state'):
            return websocket.client_state.name != 'DISCONNECTED'
        # Fallback: assume connected if no state info available
        return True
    except Exception:
        # If we can't determine the state, assume disconnected to be safe
        return False


class RedisManager:
    """Redis connection and pub/sub manager."""
    
    def __init__(self):
        self.redis: redis.Redis = None
        self.pubsub: redis.client.PubSub = None
        self.websocket_connections: Dict[str, Set[WebSocket]] = {}
        self._listening = False
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(settings.REDIS_URL)
            self.pubsub = self.redis.pubsub()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Disconnected from Redis")
    
    async def subscribe_to_board(self, board_id: str):
        """Subscribe to board updates."""
        channel = f"board:{board_id}"
        await self.pubsub.subscribe(channel)
        logger.info("Subscribed to board channel", board_id=board_id, channel=channel)
    
    async def unsubscribe_from_board(self, board_id: str):
        """Unsubscribe from board updates."""
        channel = f"board:{board_id}"
        await self.pubsub.unsubscribe(channel)
        logger.info("Unsubscribed from board channel", board_id=board_id, channel=channel)
    
    async def publish_board_update(self, board_id: str, message: Dict[str, Any]):
        """Publish board update to Redis."""
        channel = f"board:{board_id}"
        await self.redis.publish(channel, json.dumps(message))
        logger.info("Published board update", board_id=board_id, channel=channel)
    
    async def listen_for_messages(self):
        """Listen for Redis messages and broadcast to WebSocket connections."""
        if self._listening:
            return
        
        self._listening = True
        logger.info("Started listening for Redis messages")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode()
                    data = json.loads(message["data"])
                    
                    # Extract board_id from channel (format: board:{board_id})
                    board_id = channel.split(":")[1]
                    
                    # Broadcast to all WebSocket connections for this board
                    await self._broadcast_to_board(board_id, data)
                    
        except Exception as e:
            logger.error("Error listening for Redis messages", error=str(e))
        finally:
            self._listening = False
    
    async def _broadcast_to_board(self, board_id: str, message: Dict[str, Any]):
        """Broadcast message to all WebSocket connections for a board."""
        if board_id not in self.websocket_connections:
            logger.warning("No connections found for board", board_id=board_id)
            return
        
        connections = self.websocket_connections[board_id].copy()
        if not connections:
            logger.warning("No active connections for board", board_id=board_id)
            return
        
        logger.info("Broadcasting message to board", board_id=board_id, connection_count=len(connections), message_type=message.get("type"))
        
        # Send message to all connected clients with connection state checking
        disconnected = set()
        for websocket in connections:
            try:
                # Check if WebSocket is still open before sending
                if not is_websocket_connected(websocket):
                    logger.debug("Skipping disconnected WebSocket", board_id=board_id)
                    disconnected.add(websocket)
                    continue
                
                await websocket.send_text(json.dumps(message))
                logger.debug("Message sent to WebSocket", board_id=board_id)
            except Exception as e:
                # Handle specific WebSocket errors
                if "ConnectionClosedError" in str(type(e)) or "ConnectionClosed" in str(type(e)):
                    logger.debug("WebSocket connection closed", board_id=board_id, error=str(e))
                else:
                    logger.warning("Failed to send message to WebSocket", board_id=board_id, error=str(e))
                disconnected.add(websocket)
        
        # Remove disconnected connections
        for websocket in disconnected:
            await self.remove_connection(board_id, websocket)
        
        logger.info("Broadcast completed", board_id=board_id, sent_to=len(connections) - len(disconnected), failed=len(disconnected))
    
    async def add_connection(self, board_id: str, websocket: WebSocket):
        """Add WebSocket connection for a board."""
        if board_id not in self.websocket_connections:
            self.websocket_connections[board_id] = set()
            # Subscribe to Redis channel for this board
            await self.subscribe_to_board(board_id)
        
        self.websocket_connections[board_id].add(websocket)
        logger.info("Added WebSocket connection", board_id=board_id, total_connections=len(self.websocket_connections[board_id]))
    
    async def remove_connection(self, board_id: str, websocket: WebSocket):
        """Remove WebSocket connection for a board."""
        if board_id in self.websocket_connections:
            self.websocket_connections[board_id].discard(websocket)
            
            # If no more connections for this board, unsubscribe from Redis
            if not self.websocket_connections[board_id]:
                await self.unsubscribe_from_board(board_id)
                del self.websocket_connections[board_id]
            
            logger.info("Removed WebSocket connection", board_id=board_id, remaining_connections=len(self.websocket_connections.get(board_id, set())))


# Global Redis manager instance
redis_manager = RedisManager()
