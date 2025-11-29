"""
List endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.list import ListSchema, ListCreate, ListUpdate, ListReorder
from app.services.list import list_service
from app.services.board import board_service

logger = structlog.get_logger()
router = APIRouter()


@router.post(response_model=ListSchema, status_code=status.HTTP_201_CREATED)
async def create_list(
    list_in: ListCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new list."""
    # Check user access to board
    has_access = await board_service.check_user_access(db, list_in.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    list_obj = await list_service.create(db, list_in)
    
    # Broadcast list creation to all connected users
    from app.core.redis import redis_manager
    broadcast_message = {
        "type": "list_created",
        "list_id": str(list_obj.id),
        "data": {
            "id": str(list_obj.id),
            "title": list_obj.title,
            "position": list_obj.position,
            "board_id": str(list_obj.board_id),
            "cards": []
        },
        "user_id": str(current_user.id),
        "timestamp": list_obj.created_at.isoformat()
    }
    await redis_manager.publish_board_update(str(list_in.board_id), broadcast_message)
    
    # Return list with relationships
    return await list_service.get_by_id(db, list_obj.id)


@router.get("/{list_id}", response_model=ListSchema)
async def get_list(
    list_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list by ID."""
    list_obj = await list_service.get_by_id(db, list_id)
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, list_obj.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return list_obj


@router.patch("/{list_id}", response_model=ListSchema)
async def update_list(
    list_id: UUID,
    list_in: ListUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update list."""
    list_obj = await list_service.get_by_id(db, list_id)
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, list_obj.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check user permissions for updates
    user_role = await board_service.get_user_role(db, list_obj.board_id, current_user.id)
    if user_role not in ["owner", "admin", "member"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update list"
        )
    
    list_obj = await list_service.update(db, list_obj, list_in)
    
    # Broadcast list update to all connected users
    from app.core.redis import redis_manager
    broadcast_message = {
        "type": "list_updated",
        "list_id": str(list_obj.id),
        "data": {
            "id": str(list_obj.id),
            "title": list_obj.title,
            "position": list_obj.position,
            "board_id": str(list_obj.board_id)
        },
        "user_id": str(current_user.id),
        "timestamp": list_obj.updated_at.isoformat()
    }
    await redis_manager.publish_board_update(str(list_obj.board_id), broadcast_message)
    
    return await list_service.get_by_id(db, list_obj.id)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete list."""
    list_obj = await list_service.get_by_id(db, list_id)
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, list_obj.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check user permissions for deletion
    user_role = await board_service.get_user_role(db, list_obj.board_id, current_user.id)
    if user_role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete list"
        )
    
    # Get board_id before deletion
    board_id = str(list_obj.board_id)
    
    await list_service.delete(db, list_obj)
    
    # Broadcast list deletion to all connected users
    from app.core.redis import redis_manager
    broadcast_message = {
        "type": "list_deleted",
        "list_id": str(list_id),
        "user_id": str(current_user.id),
        "timestamp": ""
    }
    await redis_manager.publish_board_update(board_id, broadcast_message)


@router.patch("/reorder", status_code=status.HTTP_200_OK)
async def reorder_lists(
    board_id: UUID,
    list_positions: List[ListReorder],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Reorder lists within a board."""
    # Check user access to board
    has_access = await board_service.check_user_access(db, board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Convert to dict format expected by service
    positions = [
        {"list_id": item.list_id, "position": item.position}
        for item in list_positions
    ]
    
    await list_service.reorder_lists(db, board_id, positions)
