"""
Card model and related functionality.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Card(Base):
    """Card model."""
    
    __tablename__ = "cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    list_id = Column(UUID(as_uuid=True), ForeignKey("lists.id"), nullable=False)
    position = Column(Float, nullable=False, default=0.0)  # For ordering within list
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    list = relationship("List", back_populates="cards")
    assignee = relationship("User", back_populates="assigned_cards")
    
    def __repr__(self):
        return f"<Card(id={self.id}, title={self.title}, position={self.position})>"

