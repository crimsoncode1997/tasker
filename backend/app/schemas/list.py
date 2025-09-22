"""
List-related Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.schemas.card import Card


class ListBase(BaseModel):
    """Base list schema."""
    title: str


class ListCreate(ListBase):
    """Schema for creating a list."""
    board_id: UUID
    position: Optional[float] = 0.0


class ListUpdate(BaseModel):
    """Schema for updating a list."""
    title: Optional[str] = None
    position: Optional[float] = None


class ListInDB(ListBase):
    """Schema for list data in database."""
    id: UUID
    board_id: UUID
    position: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ListSchema(ListInDB):
    """Schema for list response."""
    cards: List[Card] = []
    
    model_config = ConfigDict(from_attributes=True)


class ListReorder(BaseModel):
    """Schema for reordering lists."""
    list_id: UUID
    position: float
