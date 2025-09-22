"""
Board endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.board import Board, BoardCreate, BoardUpdate, BoardInvite
from app.services.board import board_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[Board])
async def get_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's boards."""
    boards = await board_service.get_user_boards(db, current_user.id)
    
    # Apply pagination
    return boards[skip:skip + limit]


@router.post("/", response_model=Board, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_in: BoardCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new board."""
    board = await board_service.create(db, board_in, current_user.id)
    
    # Return board with relationships
    return await board_service.get_by_id(db, board.id)


@router.get("/{board_id}", response_model=Board)
async def get_board(
    board_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get board by ID."""
    # Check user access
    has_access = await board_service.check_user_access(db, board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    board = await board_service.get_by_id(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    return board


@router.patch("/{board_id}", response_model=Board)
async def update_board(
    board_id: UUID,
    board_in: BoardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update board."""
    # Check user access and permissions
    has_access = await board_service.check_user_access(db, board_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_role = await board_service.get_user_role(db, board_id, current_user.id)
    if user_role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update board"
        )
    
    board = await board_service.get_by_id(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    board = await board_service.update(db, board, board_in)
    return await board_service.get_by_id(db, board.id)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete board."""
    # Only owner can delete board
    user_role = await board_service.get_user_role(db, board_id, current_user.id)
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only board owner can delete the board"
        )
    
    board = await board_service.get_by_id(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    await board_service.delete(db, board)


@router.post("/{board_id}/invite", status_code=status.HTTP_201_CREATED)
async def invite_user_to_board(
    board_id: UUID,
    invite_data: BoardInvite,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite user to board."""
    # Check user permissions
    user_role = await board_service.get_user_role(db, board_id, current_user.id)
    if user_role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to invite users"
        )
    
    # Verify board exists
    board = await board_service.get_by_id(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    await board_service.invite_user(db, board_id, invite_data.email, invite_data.role)

