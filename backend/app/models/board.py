"""
Board model and related functionality.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Board(Base):
    """Board model."""
    
    __tablename__ = "boards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="owned_boards")
    members = relationship("BoardMember", back_populates="board", cascade="all, delete-orphan")
    lists = relationship("List", back_populates="board", cascade="all, delete-orphan", order_by="List.position")
    
    def __repr__(self):
        return f"<Board(id={self.id}, title={self.title})>"


class BoardMember(Base):
    """Board membership model."""
    
    __tablename__ = "board_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # owner, admin, member
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    board = relationship("Board", back_populates="members")
    user = relationship("User", back_populates="board_memberships")
    
    def __repr__(self):
        return f"<BoardMember(board_id={self.board_id}, user_id={self.user_id}, role={self.role})>"

