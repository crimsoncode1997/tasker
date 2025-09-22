"""
List service for business logic.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import structlog

from app.models.list import List as ListModel
from app.models.board import Board
from app.schemas.list import ListCreate, ListUpdate

logger = structlog.get_logger()


class ListService:
    """List service class."""
    
    async def get_by_id(self, db: AsyncSession, list_id: UUID) -> Optional[ListModel]:
        """Get list by ID with relationships."""
        result = await db.execute(
            select(ListModel)
            .options(
                selectinload(ListModel.board),
                selectinload(ListModel.cards).selectinload("assignee")
            )
            .where(ListModel.id == list_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_board_id(self, db: AsyncSession, board_id: UUID) -> List[ListModel]:
        """Get all lists for a board ordered by position."""
        result = await db.execute(
            select(ListModel)
            .options(selectinload(ListModel.cards).selectinload("assignee"))
            .where(ListModel.board_id == board_id)
            .order_by(ListModel.position)
        )
        return list(result.scalars().all())
    
    async def create(self, db: AsyncSession, list_in: ListCreate) -> ListModel:
        """Create a new list."""
        # Get the next position
        max_position = await self._get_max_position(db, list_in.board_id)
        position = max_position + 1.0 if max_position is not None else 1.0
        
        list_obj = ListModel(
            title=list_in.title,
            board_id=list_in.board_id,
            position=position,
        )
        
        db.add(list_obj)
        await db.commit()
        await db.refresh(list_obj)
        
        logger.info("List created", list_id=str(list_obj.id), board_id=str(list_in.board_id))
        return list_obj
    
    async def update(self, db: AsyncSession, list_obj: ListModel, list_in: ListUpdate) -> ListModel:
        """Update list."""
        update_data = list_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(list_obj, field, value)
        
        db.add(list_obj)
        await db.commit()
        await db.refresh(list_obj)
        
        logger.info("List updated", list_id=str(list_obj.id))
        return list_obj
    
    async def delete(self, db: AsyncSession, list_obj: ListModel) -> None:
        """Delete list."""
        await db.delete(list_obj)
        await db.commit()
        
        logger.info("List deleted", list_id=str(list_obj.id))
    
    async def reorder_lists(self, db: AsyncSession, board_id: UUID, list_positions: List[dict]) -> None:
        """Reorder lists within a board."""
        for item in list_positions:
            list_id = item["list_id"]
            position = item["position"]
            
            result = await db.execute(
                select(ListModel).where(
                    and_(ListModel.id == list_id, ListModel.board_id == board_id)
                )
            )
            list_obj = result.scalar_one_or_none()
            
            if list_obj:
                list_obj.position = position
                db.add(list_obj)
        
        await db.commit()
        logger.info("Lists reordered", board_id=str(board_id))
    
    async def _get_max_position(self, db: AsyncSession, board_id: UUID) -> Optional[float]:
        """Get the maximum position for lists in a board."""
        result = await db.execute(
            select(ListModel.position)
            .where(ListModel.board_id == board_id)
            .order_by(ListModel.position.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


# Create service instance
list_service = ListService()
