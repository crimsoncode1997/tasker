"""
Notification service for business logic.
"""
import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
import structlog

from app.models.notification import Notification
from app.models.user import User

logger = structlog.get_logger()


class NotificationService:
    """Notification service class."""
    
    async def create_notification(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        notification_type: str, 
        title: str, 
        message: str, 
        data: dict = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=json.dumps(data) if data else None
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        logger.info("Notification created", notification_id=str(notification.id), user_id=str(user_id))
        return notification
    
    async def get_user_notifications(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Notification]:
        """Get user notifications."""
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def mark_as_read(self, db: AsyncSession, notification_id: UUID, user_id: UUID) -> Notification:
        """Mark notification as read."""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            
            logger.info("Notification marked as read", notification_id=str(notification_id))
        
        return notification
    
    async def mark_all_as_read(self, db: AsyncSession, user_id: UUID) -> int:
        """Mark all user notifications as read."""
        from datetime import datetime
        
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.add(notification)
            count += 1
        
        await db.commit()
        logger.info("All notifications marked as read", user_id=str(user_id), count=count)
        return count
    
    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        """Get count of unread notifications."""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        return len(notifications)


# Create service instance
notification_service = NotificationService()
