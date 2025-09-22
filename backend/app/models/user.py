"""
User model and related functionality.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owned_boards = relationship("Board", back_populates="owner", cascade="all, delete-orphan")
    board_memberships = relationship("BoardMember", back_populates="user", cascade="all, delete-orphan")
    assigned_cards = relationship("Card", back_populates="assignee")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

