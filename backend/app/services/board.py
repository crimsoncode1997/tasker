"""
Board service for business logic.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import structlog

from app.models.board import Board, BoardMember
from app.models.user import User
from app.schemas.board import BoardCreate, BoardUpdate, BoardInvite

logger = structlog.get_logger()


class BoardService:
    """Board service class."""
    
    async def get_by_id(self, db: AsyncSession, board_id: UUID) -> Optional[Board]:
        """Get board by ID with relationships."""
        result = await db.execute(
            select(Board)
            .options(
                selectinload(Board.owner),
                selectinload(Board.lists).selectinload("cards").selectinload("assignee"),
                selectinload(Board.members).selectinload("user")
            )
            .where(Board.id == board_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_boards(self, db: AsyncSession, user_id: UUID) -> List[Board]:
        """Get boards accessible by user (owned or member)."""
        result = await db.execute(
            select(Board)
            .join(BoardMember, Board.id == BoardMember.board_id, isouter=True)
            .where(
                (Board.owner_id == user_id) | (BoardMember.user_id == user_id)
            )
            .order_by(Board.updated_at.desc())
        )
        return list(result.scalars().all())
    
    async def create(self, db: AsyncSession, board_in: BoardCreate, owner_id: UUID) -> Board:
        """Create a new board."""
        board = Board(
            title=board_in.title,
            description=board_in.description,
            owner_id=owner_id,
        )
        
        db.add(board)
        await db.commit()
        await db.refresh(board)
        
        # Add owner as admin member
        member = BoardMember(
            board_id=board.id,
            user_id=owner_id,
            role="owner"
        )
        db.add(member)
        await db.commit()
        
        logger.info("Board created", board_id=str(board.id), owner_id=str(owner_id))
        return board
    
    async def update(self, db: AsyncSession, board: Board, board_in: BoardUpdate) -> Board:
        """Update board."""
        update_data = board_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(board, field, value)
        
        db.add(board)
        await db.commit()
        await db.refresh(board)
        
        logger.info("Board updated", board_id=str(board.id))
        return board
    
    async def delete(self, db: AsyncSession, board: Board) -> None:
        """Delete board."""
        await db.delete(board)
        await db.commit()
        
        logger.info("Board deleted", board_id=str(board.id))
    
    async def check_user_access(self, db: AsyncSession, board_id: UUID, user_id: UUID) -> bool:
        """Check if user has access to board."""
        result = await db.execute(
            select(Board)
            .join(BoardMember, Board.id == BoardMember.board_id, isouter=True)
            .where(
                and_(
                    Board.id == board_id,
                    (Board.owner_id == user_id) | (BoardMember.user_id == user_id)
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def get_user_role(self, db: AsyncSession, board_id: UUID, user_id: UUID) -> Optional[str]:
        """Get user's role in board."""
        # Check if owner
        result = await db.execute(
            select(Board).where(Board.id == board_id, Board.owner_id == user_id)
        )
        if result.scalar_one_or_none():
            return "owner"
        
        # Check membership
        result = await db.execute(
            select(BoardMember).where(
                BoardMember.board_id == board_id,
                BoardMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        return member.role if member else None
    
    async def invite_user(self, db: AsyncSession, board_id: UUID, email: str, role: str = "member") -> None:
        """Invite user to board by email."""
        # Get user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already a member
        result = await db.execute(
            select(BoardMember).where(
                BoardMember.board_id == board_id,
                BoardMember.user_id == user.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this board"
            )
        
        # Add member
        member = BoardMember(
            board_id=board_id,
            user_id=user.id,
            role=role
        )
        db.add(member)
        await db.commit()
        
        logger.info("User invited to board", board_id=str(board_id), user_id=str(user.id), role=role)


# Create service instance
board_service = BoardService()

