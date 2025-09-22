"""
Card service for business logic.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import structlog

from app.models.card import Card
from app.models.list import List as ListModel
from app.schemas.card import CardCreate, CardUpdate, CardMove, CardReorder

logger = structlog.get_logger()


class CardService:
    """Card service class."""
    
    async def get_by_id(self, db: AsyncSession, card_id: UUID) -> Optional[Card]:
        """Get card by ID with relationships."""
        result = await db.execute(
            select(Card)
            .options(
                selectinload(Card.list),
                selectinload(Card.assignee)
            )
            .where(Card.id == card_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_list_id(self, db: AsyncSession, list_id: UUID) -> List[Card]:
        """Get all cards for a list ordered by position."""
        result = await db.execute(
            select(Card)
            .options(selectinload(Card.assignee))
            .where(Card.list_id == list_id)
            .order_by(Card.position)
        )
        return list(result.scalars().all())
    
    async def create(self, db: AsyncSession, card_in: CardCreate) -> Card:
        """Create a new card."""
        # Get the next position
        max_position = await self._get_max_position(db, card_in.list_id)
        position = max_position + 1.0 if max_position is not None else 1.0
        
        card = Card(
            title=card_in.title,
            description=card_in.description,
            list_id=card_in.list_id,
            position=position,
            assignee_id=card_in.assignee_id,
            due_date=card_in.due_date,
        )
        
        db.add(card)
        await db.commit()
        await db.refresh(card)
        
        logger.info("Card created", card_id=str(card.id), list_id=str(card_in.list_id))
        return card
    
    async def update(self, db: AsyncSession, card: Card, card_in: CardUpdate) -> Card:
        """Update card."""
        update_data = card_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(card, field, value)
        
        db.add(card)
        await db.commit()
        await db.refresh(card)
        
        logger.info("Card updated", card_id=str(card.id))
        return card
    
    async def delete(self, db: AsyncSession, card: Card) -> None:
        """Delete card."""
        await db.delete(card)
        await db.commit()
        
        logger.info("Card deleted", card_id=str(card.id))
    
    async def move_card(self, db: AsyncSession, card_move: CardMove) -> Card:
        """Move card to another list."""
        # Get card
        card = await self.get_by_id(db, card_move.card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Update position in new list
        card.list_id = card_move.list_id
        card.position = card_move.position
        
        db.add(card)
        await db.commit()
        await db.refresh(card)
        
        logger.info("Card moved", card_id=str(card.id), new_list_id=str(card_move.list_id))
        return card
    
    async def reorder_cards(self, db: AsyncSession, list_id: UUID, card_positions: List[dict]) -> None:
        """Reorder cards within a list."""
        for item in card_positions:
            card_id = item["card_id"]
            position = item["position"]
            
            result = await db.execute(
                select(Card).where(
                    and_(Card.id == card_id, Card.list_id == list_id)
                )
            )
            card = result.scalar_one_or_none()
            
            if card:
                card.position = position
                db.add(card)
        
        await db.commit()
        logger.info("Cards reordered", list_id=str(list_id))
    
    async def _get_max_position(self, db: AsyncSession, list_id: UUID) -> Optional[float]:
        """Get the maximum position for cards in a list."""
        result = await db.execute(
            select(Card.position)
            .where(Card.list_id == list_id)
            .order_by(Card.position.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


# Create service instance
card_service = CardService()
