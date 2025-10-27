"""
Board-related Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import User
from app.schemas.list import ListSchema


class BoardBase(BaseModel):
    """Base board schema."""
    title: str
    description: Optional[str] = None


class BoardCreate(BoardBase):
    """Schema for creating a board."""
    pass


class BoardUpdate(BaseModel):
    """Schema for updating a board."""
    title: Optional[str] = None
    description: Optional[str] = None


class BoardInDB(BoardBase):
    """Schema for board data in database."""
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class Board(BoardInDB):
    """Schema for board response."""
    owner: User
    lists: List[ListSchema] = Field(default_factory=list)
    user_role: Optional[str] = None  # Role of the current user in this board
    
    model_config = ConfigDict(from_attributes=True)


class BoardMemberCreate(BaseModel):
    """Schema for adding a board member."""
    user_id: UUID
    role: str = "member"


class BoardInvite(BaseModel):
    """Schema for inviting a user to a board."""
    email: str
    role: str = "member"
