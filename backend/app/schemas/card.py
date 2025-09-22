"""
Card-related Pydantic schemas.
"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.schemas.user import User


class CardBase(BaseModel):
    """Base card schema."""
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None


class CardCreate(CardBase):
    """Schema for creating a card."""
    list_id: UUID
    position: Optional[float] = 0.0
    assignee_id: Optional[UUID] = None


class CardUpdate(BaseModel):
    """Schema for updating a card."""
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[float] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None


class CardInDB(CardBase):
    """Schema for card data in database."""
    id: UUID
    list_id: UUID
    position: float
    assignee_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Card(CardInDB):
    """Schema for card response."""
    assignee: Optional[User] = None
    
    model_config = ConfigDict(from_attributes=True)


class CardMove(BaseModel):
    """Schema for moving a card between lists."""
    card_id: UUID
    list_id: UUID
    position: float


class CardReorder(BaseModel):
    """Schema for reordering cards within a list."""
    card_id: UUID
    position: float
