"""
Notification endpoints.
"""
import json
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
import structlog

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.notification import Notification
from app.services.notification import notification_service

logger = structlog.get_logger()
router = APIRouter()


@router.get(response_model=List[dict])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user notifications."""
    notifications = await notification_service.get_user_notifications(
        db, current_user.id, limit, skip
    )
    
    return [
        {
            "id": str(notification.id),
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "data": json.loads(notification.data) if notification.data else None,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
            "read_at": notification.read_at.isoformat() if notification.read_at else None
        }
        for notification in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notifications."""
    count = await notification_service.get_unread_count(db, current_user.id)
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read."""
    notification = await notification_service.mark_as_read(
        db, notification_id, current_user.id
    )
    
    return {
        "id": str(notification.id),
        "is_read": notification.is_read,
        "read_at": notification.read_at.isoformat() if notification.read_at else None
    }


@router.patch("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read."""
    count = await notification_service.mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete notification."""
    from sqlalchemy import delete
    
    result = await db.execute(
        delete(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    await db.commit()
    return {"message": "Notification deleted"}


