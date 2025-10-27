"""
Card endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.card import Card, CardCreate, CardUpdate, CardMove, CardReorder
from app.services.card import card_service
from app.services.board import board_service
from app.services.list import list_service

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=Card, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_in: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new card."""
    # Get list to check board access
    list_obj = await list_service.get_by_id(db, card_in.list_id)
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
    
    card = await card_service.create(db, card_in)
    
    # Broadcast card creation to all connected users
    from app.core.redis import redis_manager
    broadcast_message = {
        "type": "card_created",
        "card_id": str(card.id),
        "data": {
            "id": str(card.id),
            "title": card.title,
            "description": card.description,
            "list_id": str(card.list_id),
            "position": card.position,
            "assignee_id": str(card.assignee_id) if card.assignee_id else None,
            "due_date": card.due_date.isoformat() if card.due_date else None
        },
        "user_id": str(current_user.id),
        "timestamp": card.created_at.isoformat()
    }
    await redis_manager.publish_board_update(str(list_obj.board_id), broadcast_message)
    
    # Return card with relationships
    return await card_service.get_by_id(db, card.id)


@router.patch("/move", response_model=Card)
async def move_card(
    card_move: CardMove,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Move card to another list."""
    # Get source card
    source_card = await card_service.get_by_id(db, card_move.card_id)
    if not source_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check user access to source board
    has_access = await board_service.check_user_access(db, source_card.list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get destination list and check access
    dest_list = await list_service.get_by_id(db, card_move.list_id)
    if not dest_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination list not found"
        )
    
    has_access = await board_service.check_user_access(db, dest_list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to destination board"
        )
    
    card = await card_service.move_card(db, card_move)
    return await card_service.get_by_id(db, card.id)


@router.patch("/reorder", status_code=status.HTTP_200_OK)
async def reorder_cards(
    list_id: UUID,
    card_positions: List[CardReorder],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Reorder cards within a list."""
    # Get list to check board access
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
    
    # Convert to dict format expected by service
    positions = [
        {"card_id": item.card_id, "position": item.position}
        for item in card_positions
    ]
    
    await card_service.reorder_cards(db, list_id, positions)


@router.get("/{card_id}", response_model=Card)
async def get_card(
    card_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get card by ID."""
    card = await card_service.get_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, card.list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return card


@router.patch("/{card_id}", response_model=Card)
async def update_card(
    card_id: UUID,
    card_in: CardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update card."""
    card = await card_service.get_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, card.list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    card = await card_service.update(db, card, card_in)
    return await card_service.get_by_id(db, card.id)


@router.patch("/{card_id}/assign/{user_id}", response_model=Card)
async def assign_card(
    card_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a card to a user."""
    # Get card
    card = await card_service.get_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, card.list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if user is a member of the board
    user_role = await board_service.get_user_role(db, card.list.board_id, user_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this board"
        )
    
    # Update card assignee
    from app.schemas.card import CardUpdate
    card_update = CardUpdate(assignee_id=user_id)
    updated_card = await card_service.update(db, card, card_update)
    
    # Broadcast assignment via WebSocket
    from app.core.redis import redis_manager
    assignment_message = {
        "type": "card_assigned",
        "card_id": str(card_id),
        "assignee_id": str(user_id),
        "user_id": str(current_user.id),
        "timestamp": updated_card.updated_at.isoformat()
    }
    await redis_manager.publish_board_update(str(card.list.board_id), assignment_message)
    
    logger.info("Card assigned", card_id=str(card_id), assignee_id=str(user_id), assigned_by=str(current_user.id))
    
    return await card_service.get_by_id(db, updated_card.id)


@router.patch("/{card_id}/unassign", response_model=Card)
async def unassign_card(
    card_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Unassign a card from its current assignee."""
    # Get card
    card = await card_service.get_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, card.list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update card to remove assignee
    from app.schemas.card import CardUpdate
    card_update = CardUpdate(assignee_id=None)
    updated_card = await card_service.update(db, card, card_update)
    
    # Broadcast unassignment via WebSocket
    from app.core.redis import redis_manager
    unassignment_message = {
        "type": "card_unassigned",
        "card_id": str(card_id),
        "user_id": str(current_user.id),
        "timestamp": updated_card.updated_at.isoformat()
    }
    await redis_manager.publish_board_update(str(card.list.board_id), unassignment_message)
    
    logger.info("Card unassigned", card_id=str(card_id), unassigned_by=str(current_user.id))
    
    return await card_service.get_by_id(db, updated_card.id)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete card."""
    card = await card_service.get_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check user access to board
    has_access = await board_service.check_user_access(db, card.list.board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await card_service.delete(db, card)

