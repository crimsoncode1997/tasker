"""
WebSocket endpoints for real-time board collaboration.
"""
import json
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.routing import APIRouter
import structlog

from app.core.redis import redis_manager
from app.core.security import verify_token
from app.core.database import get_db
from app.services.board import board_service
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()


async def get_current_user_from_token(token: str, db: AsyncSession):
    """Get current user from JWT token."""
    # Verify token and get user
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    # Get user from database
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.websocket("/ws/board/{board_id}")
async def websocket_endpoint(websocket: WebSocket, board_id: str):
    """WebSocket endpoint for real-time board collaboration."""
    await websocket.accept()
    
    # Create a separate database session for WebSocket operations
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            if not token:
                await websocket.close(code=4001, reason="Missing authentication token")
                return
            
            # Authenticate user
            try:
                user = await get_current_user_from_token(token, db)
            except HTTPException as e:
                await websocket.close(code=4001, reason=f"Authentication failed: {e.detail}")
                return
            
            # Check if user has access to the board
            from uuid import UUID
            try:
                board_uuid = UUID(board_id)
            except ValueError:
                logger.error("Invalid board ID format", board_id=board_id)
                await websocket.close(code=4000, reason="Invalid board ID format")
                return
            
            logger.info("Checking board access", board_id=board_id, user_id=str(user.id))
            has_access = await board_service.check_user_access(db, board_uuid, user.id)
            logger.info("Board access result", board_id=board_id, user_id=str(user.id), has_access=has_access)
            if not has_access:
                logger.warning("Access denied to board", board_id=board_id, user_id=str(user.id))
                await websocket.close(code=4003, reason="Access denied to board")
                return
            
            # Add connection to Redis manager
            await redis_manager.add_connection(board_id, websocket)
            
            logger.info("WebSocket connected", board_id=board_id, user_id=str(user.id))
            
            # Send welcome message with board data
            welcome_message = {
                "type": "connection",
                "message": f"Connected to board {board_id}",
                "user_id": str(user.id),
                "user_name": user.full_name,
                "board_id": board_id
            }
            await websocket.send_text(json.dumps(welcome_message))
            
            # Send current board state to newly connected user
            try:
                board = await board_service.get_by_id(db, board_uuid)
                if board:
                    board_state = {
                        "type": "board_state",
                        "board": {
                            "id": str(board.id),
                            "title": board.title,
                            "description": board.description,
                            "lists": [
                                {
                                    "id": str(list.id),
                                    "title": list.title,
                                    "position": list.position,
                                    "cards": [
                                        {
                                            "id": str(card.id),
                                            "title": card.title,
                                            "description": card.description,
                                            "position": card.position,
                                            "assignee_id": str(card.assignee_id) if card.assignee_id else None,
                                            "assignee": {
                                                "id": str(card.assignee.id),
                                                "full_name": card.assignee.full_name,
                                                "email": card.assignee.email
                                            } if card.assignee else None,
                                            "due_date": card.due_date.isoformat() if card.due_date else None,
                                            "created_at": card.created_at.isoformat(),
                                            "updated_at": card.updated_at.isoformat()
                                        } for card in list.cards
                                    ]
                                } for list in board.lists
                            ]
                        }
                    }
                    await websocket.send_text(json.dumps(board_state))
            except Exception as e:
                logger.error("Error sending board state", error=str(e))
            
            # Listen for messages from client
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Process different message types
                    await process_board_message(board_id, user.id, message, db)
                    
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    error_message = {
                        "type": "error",
                        "message": "Invalid JSON format"
                    }
                    await websocket.send_text(json.dumps(error_message))
                except Exception as e:
                    logger.error("Error processing WebSocket message", error=str(e))
                    error_message = {
                        "type": "error",
                        "message": "Internal server error"
                    }
                    await websocket.send_text(json.dumps(error_message))
        
        except Exception as e:
            logger.error("WebSocket connection error", error=str(e))
            await websocket.close(code=4000, reason="Internal server error")
        
        finally:
            # Remove connection from Redis manager
            await redis_manager.remove_connection(board_id, websocket)
            logger.info("WebSocket disconnected", board_id=board_id)


@router.websocket("/ws/notifications")
async def global_notifications_endpoint(websocket: WebSocket):
    """WebSocket endpoint for global user notifications."""
    await websocket.accept()
    
    # Create a separate database session for WebSocket operations
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            if not token:
                await websocket.close(code=4001, reason="Missing authentication token")
                return
            
            # Authenticate user
            try:
                user = await get_current_user_from_token(token, db)
            except HTTPException as e:
                await websocket.close(code=4001, reason=f"Authentication failed: {e.detail}")
                return
            
            # Add connection to Redis manager for user-specific notifications
            await redis_manager.add_connection(f"user:{user.id}", websocket)
            
            logger.info("Global notification WebSocket connected", user_id=str(user.id))
            
            # Send welcome message
            welcome_message = {
                "type": "connection",
                "message": "Connected to notifications",
                "user_id": str(user.id),
                "user_name": user.full_name
            }
            await websocket.send_text(json.dumps(welcome_message))
            
            # Keep connection alive
            while True:
                try:
                    # Just keep the connection alive - messages will be sent via Redis
                    data = await websocket.receive_text()
                    # Echo back any messages received (for ping/pong)
                    await websocket.send_text(data)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error("Error in global notification WebSocket", error=str(e))
                    break
        
        except Exception as e:
            logger.error("Global notification WebSocket connection error", error=str(e))
            await websocket.close(code=4000, reason="Internal server error")
        
        finally:
            # Remove connection from Redis manager
            await redis_manager.remove_connection(f"user:{user.id}", websocket)
            logger.info("Global notification WebSocket disconnected", user_id=str(user.id))


async def process_board_message(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Process incoming board message and broadcast to other users."""
    message_type = message.get("type")
    
    if message_type == "card_move":
        # Handle card movement
        await handle_card_move(board_id, user_id, message, db)
    elif message_type == "card_update":
        # Handle card updates
        await handle_card_update(board_id, user_id, message, db)
    elif message_type == "card_assign":
        # Handle card assignment
        await handle_card_assign(board_id, user_id, message, db)
    elif message_type == "list_update":
        # Handle list updates
        await handle_list_update(board_id, user_id, message, db)
    elif message_type == "board_update":
        # Handle board updates
        await handle_board_update(board_id, user_id, message, db)
    elif message_type == "user_typing":
        # Handle typing indicators
        await handle_user_typing(board_id, user_id, message)
    else:
        logger.warning("Unknown message type", message_type=message_type)


async def handle_card_move(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle card movement and broadcast to other users."""
    try:
        # Import card service
        from app.services.card import card_service
        
        card_id = message.get("card_id")
        new_list_id = message.get("new_list_id")
        new_position = message.get("new_position")
        
        if not all([card_id, new_list_id, new_position is not None]):
            return
        
        # Update card in database
        from app.schemas.card import CardMove
        card_move = CardMove(
            card_id=card_id,
            new_list_id=new_list_id,
            new_position=new_position
        )
        
        updated_card = await card_service.move_card(db, card_move, user_id)
        
        # Broadcast update to other users
        broadcast_message = {
            "type": "card_moved",
            "card_id": card_id,
            "new_list_id": new_list_id,
            "new_position": new_position,
            "user_id": str(user_id),
            "timestamp": updated_card.updated_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling card move", error=str(e))


async def handle_card_update(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle card updates and broadcast to other users."""
    try:
        from app.services.card import card_service
        
        card_id = message.get("card_id")
        update_data = message.get("data", {})
        
        if not card_id:
            return
        
        # Update card in database
        updated_card = await card_service.update(db, card_id, update_data, user_id)
        
        # Broadcast update to other users
        broadcast_message = {
            "type": "card_updated",
            "card_id": card_id,
            "data": update_data,
            "user_id": str(user_id),
            "timestamp": updated_card.updated_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling card update", error=str(e))


async def handle_list_update(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle list updates and broadcast to other users."""
    try:
        from app.services.list import list_service
        
        list_id = message.get("list_id")
        update_data = message.get("data", {})
        
        if not list_id:
            return
        
        # Update list in database
        updated_list = await list_service.update(db, list_id, update_data, user_id)
        
        # Broadcast update to other users
        broadcast_message = {
            "type": "list_updated",
            "list_id": list_id,
            "data": update_data,
            "user_id": str(user_id),
            "timestamp": updated_list.updated_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling list update", error=str(e))


async def handle_board_update(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle board updates and broadcast to other users."""
    try:
        update_data = message.get("data", {})
        
        # Update board in database
        from app.schemas.board import BoardUpdate
        board_update = BoardUpdate(**update_data)
        
        board = await board_service.get_by_id(db, board_id)
        if not board:
            return
        
        updated_board = await board_service.update(db, board, board_update)
        
        # Broadcast update to other users
        broadcast_message = {
            "type": "board_updated",
            "data": update_data,
            "user_id": str(user_id),
            "timestamp": updated_board.updated_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling board update", error=str(e))


async def handle_card_assign(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle card assignment and broadcast to other users."""
    try:
        from app.services.card import card_service
        
        card_id = message.get("card_id")
        assignee_id = message.get("assignee_id")
        
        if not card_id:
            return
        
        # Update card assignment in database
        card = await card_service.get_by_id(db, card_id)
        if not card:
            return
        
        from app.schemas.card import CardUpdate
        card_update = CardUpdate(assignee_id=assignee_id)
        updated_card = await card_service.update(db, card, card_update)
        
        # Broadcast assignment to other users
        broadcast_message = {
            "type": "card_assigned",
            "card_id": card_id,
            "assignee_id": assignee_id,
            "user_id": str(user_id),
            "timestamp": updated_card.updated_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling card assignment", error=str(e))


async def handle_user_typing(board_id: str, user_id: str, message: Dict[str, Any]):
    """Handle typing indicators and broadcast to other users."""
    try:
        typing_data = message.get("data", {})
        
        # Broadcast typing indicator to other users
        broadcast_message = {
            "type": "user_typing",
            "user_id": str(user_id),
            "data": typing_data,
            "timestamp": message.get("timestamp")
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling user typing", error=str(e))
