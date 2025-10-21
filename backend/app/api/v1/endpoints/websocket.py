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
    logger.info("WebSocket connection attempt", board_id=board_id)
    
    try:
        await websocket.accept()
        logger.info("WebSocket accepted", board_id=board_id)
    except Exception as e:
        logger.error("Failed to accept WebSocket", board_id=board_id, error=str(e))
        return
    
    # Create a separate database session for WebSocket operations
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            if not token:
                logger.warning("Missing authentication token", board_id=board_id)
                await websocket.close(code=4001, reason="Missing authentication token")
                return
            
            logger.info("Token received", board_id=board_id, token_length=len(token))
            
            # Authenticate user
            try:
                user = await get_current_user_from_token(token, db)
                logger.info("User authenticated", board_id=board_id, user_id=str(user.id))
            except HTTPException as e:
                logger.warning("Authentication failed", board_id=board_id, error=e.detail)
                await websocket.close(code=4001, reason=f"Authentication failed: {e.detail}")
                return
            except Exception as e:
                logger.error("Unexpected authentication error", board_id=board_id, error=str(e))
                await websocket.close(code=4001, reason="Authentication failed: Internal error")
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
            
            # Send welcome message with board data (with connection state check)
            try:
                welcome_message = {
                    "type": "connection",
                    "message": f"Connected to board {board_id}",
                    "user_id": str(user.id),
                    "user_name": user.full_name,
                    "board_id": board_id
                }
                await websocket.send_text(json.dumps(welcome_message))
                logger.info("Welcome message sent to board WebSocket", board_id=board_id, user_id=str(user.id))
            except Exception as e:
                logger.warning("Failed to send welcome message to board WebSocket", board_id=board_id, user_id=str(user.id), error=str(e))
                # Don't close the connection here, let it continue
            
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
                    # Check if WebSocket is still connected before receiving
                    if not hasattr(websocket, 'client_state') or websocket.client_state.name == 'DISCONNECTED':
                        logger.info("WebSocket disconnected, breaking message loop", board_id=board_id)
                        break
                    
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Process different message types
                    await process_board_message(board_id, user.id, message, db)
                    
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected normally", board_id=board_id)
                    break
                except json.JSONDecodeError:
                    try:
                        error_message = {
                            "type": "error",
                            "message": "Invalid JSON format"
                        }
                        await websocket.send_text(json.dumps(error_message))
                    except Exception as send_error:
                        logger.warning("Failed to send error message", error=str(send_error))
                        break
                except Exception as e:
                    logger.error("Error processing WebSocket message", error=str(e))
                    try:
                        error_message = {
                            "type": "error",
                            "message": "Internal server error"
                        }
                        await websocket.send_text(json.dumps(error_message))
                    except Exception as send_error:
                        logger.warning("Failed to send error message", error=str(send_error))
                        break
        
        except Exception as e:
            logger.error("WebSocket connection error", error=str(e))
            try:
                await websocket.close(code=4000, reason="Internal server error")
            except Exception as close_error:
                logger.warning("Failed to close WebSocket", error=str(close_error))
        
        finally:
            # Remove connection from Redis manager
            try:
                await redis_manager.remove_connection(board_id, websocket)
                logger.info("WebSocket disconnected", board_id=board_id)
            except Exception as cleanup_error:
                logger.warning("Failed to cleanup WebSocket connection", error=str(cleanup_error))


@router.websocket("/ws/notifications")
async def global_notifications_endpoint(websocket: WebSocket):
    """WebSocket endpoint for global user notifications."""
    logger.info("Global notification WebSocket connection attempt")
    
    try:
        await websocket.accept()
        logger.info("Global notification WebSocket accepted")
    except Exception as e:
        logger.error("Failed to accept global notification WebSocket", error=str(e))
        return
    
    # Create a separate database session for WebSocket operations
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            if not token:
                logger.warning("Missing authentication token for global notifications")
                await websocket.close(code=4001, reason="Missing authentication token")
                return
            
            logger.info("Global notification token received", token_length=len(token))
            
            # Authenticate user
            try:
                user = await get_current_user_from_token(token, db)
                logger.info("Global notification user authenticated", user_id=str(user.id))
            except HTTPException as e:
                logger.warning("Global notification authentication failed", error=e.detail)
                await websocket.close(code=4001, reason=f"Authentication failed: {e.detail}")
                return
            except Exception as e:
                logger.error("Unexpected global notification authentication error", error=str(e))
                await websocket.close(code=4001, reason="Authentication failed: Internal error")
                return
            
            # Add connection to Redis manager for user-specific notifications
            await redis_manager.add_connection(f"user:{user.id}", websocket)
            
            logger.info("Global notification WebSocket connected", user_id=str(user.id))
            
            # Send welcome message (with connection state check)
            try:
                welcome_message = {
                    "type": "connection",
                    "message": "Connected to notifications",
                    "user_id": str(user.id),
                    "user_name": user.full_name
                }
                await websocket.send_text(json.dumps(welcome_message))
                logger.info("Welcome message sent to global notification WebSocket", user_id=str(user.id))
            except Exception as e:
                logger.warning("Failed to send welcome message to global notification WebSocket", user_id=str(user.id), error=str(e))
                # Don't close the connection here, let it continue
            
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
            try:
                await websocket.close(code=4000, reason="Internal server error")
            except Exception as close_error:
                logger.warning("Failed to close global notification WebSocket", error=str(close_error))
        
        finally:
            # Remove connection from Redis manager
            try:
                await redis_manager.remove_connection(f"user:{user.id}", websocket)
                logger.info("Global notification WebSocket disconnected", user_id=str(user.id))
            except Exception as cleanup_error:
                logger.warning("Failed to cleanup global notification WebSocket connection", error=str(cleanup_error))


async def process_board_message(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Process incoming board message and broadcast to other users."""
    message_type = message.get("type")
    
    logger.info("Processing board message", board_id=board_id, user_id=str(user_id), message_type=message_type)
    
    try:
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
        elif message_type == "list_create":
            # Handle list creation
            await handle_list_create(board_id, user_id, message, db)
        elif message_type == "card_create":
            # Handle card creation
            await handle_card_create(board_id, user_id, message, db)
        elif message_type == "list_delete":
            # Handle list deletion
            await handle_list_delete(board_id, user_id, message, db)
        elif message_type == "card_delete":
            # Handle card deletion
            await handle_card_delete(board_id, user_id, message, db)
        elif message_type == "board_delete":
            # Handle board deletion
            await handle_board_delete(board_id, user_id, message, db)
        else:
            logger.warning("Unknown message type", message_type=message_type)
    except Exception as e:
        logger.error("Error processing board message", board_id=board_id, user_id=str(user_id), error=str(e))


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


async def handle_list_create(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle list creation and broadcast to other users."""
    try:
        from app.services.list import list_service
        
        list_data = message.get("data", {})
        if not list_data.get("title"):
            return
        
        # Create list in database
        from app.schemas.list import ListCreate
        list_create = ListCreate(
            title=list_data["title"],
            board_id=board_id,
            position=list_data.get("position", 0)
        )
        
        new_list = await list_service.create(db, list_create, user_id)
        
        # Broadcast creation to other users
        broadcast_message = {
            "type": "list_created",
            "list_id": str(new_list.id),
            "data": {
                "id": str(new_list.id),
                "title": new_list.title,
                "position": new_list.position,
                "board_id": str(new_list.board_id),
                "cards": []
            },
            "user_id": str(user_id),
            "timestamp": new_list.created_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling list creation", error=str(e))


async def handle_card_create(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle card creation and broadcast to other users."""
    try:
        from app.services.card import card_service
        
        card_data = message.get("data", {})
        if not card_data.get("title") or not card_data.get("list_id"):
            return
        
        # Create card in database
        from app.schemas.card import CardCreate
        card_create = CardCreate(
            title=card_data["title"],
            description=card_data.get("description"),
            list_id=card_data["list_id"],
            position=card_data.get("position", 0),
            assignee_id=card_data.get("assignee_id"),
            due_date=card_data.get("due_date")
        )
        
        new_card = await card_service.create(db, card_create, user_id)
        
        # Broadcast creation to other users
        broadcast_message = {
            "type": "card_created",
            "card_id": str(new_card.id),
            "data": {
                "id": str(new_card.id),
                "title": new_card.title,
                "description": new_card.description,
                "list_id": str(new_card.list_id),
                "position": new_card.position,
                "assignee_id": str(new_card.assignee_id) if new_card.assignee_id else None,
                "due_date": new_card.due_date.isoformat() if new_card.due_date else None
            },
            "user_id": str(user_id),
            "timestamp": new_card.created_at.isoformat()
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling card creation", error=str(e))


async def handle_list_delete(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle list deletion and broadcast to other users."""
    try:
        from app.services.list import list_service
        
        list_id = message.get("list_id")
        if not list_id:
            return
        
        # Delete list from database
        await list_service.delete(db, list_id, user_id)
        
        # Broadcast deletion to other users
        broadcast_message = {
            "type": "list_deleted",
            "list_id": list_id,
            "user_id": str(user_id),
            "timestamp": message.get("timestamp", "")
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling list deletion", error=str(e))


async def handle_card_delete(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle card deletion and broadcast to other users."""
    try:
        from app.services.card import card_service
        
        card_id = message.get("card_id")
        if not card_id:
            return
        
        # Delete card from database
        await card_service.delete(db, card_id, user_id)
        
        # Broadcast deletion to other users
        broadcast_message = {
            "type": "card_deleted",
            "card_id": card_id,
            "user_id": str(user_id),
            "timestamp": message.get("timestamp", "")
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
    except Exception as e:
        logger.error("Error handling card deletion", error=str(e))


async def handle_board_delete(board_id: str, user_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle board deletion and redirect all connected users."""
    try:
        from app.services.board import board_service
        
        # Get board to verify ownership
        board = await board_service.get_by_id(db, board_id)
        if not board:
            return
        
        # Only owner can delete board
        if board.owner_id != user_id:
            logger.warning("Non-owner attempted to delete board", board_id=board_id, user_id=str(user_id))
            return
        
        # Delete board from database
        await board_service.delete(db, board)
        
        # Broadcast board deletion to all connected users
        broadcast_message = {
            "type": "board_deleted",
            "board_id": board_id,
            "user_id": str(user_id),
            "timestamp": message.get("timestamp", ""),
            "redirect": True  # Signal to redirect users
        }
        
        await redis_manager.publish_board_update(board_id, broadcast_message)
        
        logger.info("Board deleted and users notified", board_id=board_id, user_id=str(user_id))
        
    except Exception as e:
        logger.error("Error handling board deletion", error=str(e))
