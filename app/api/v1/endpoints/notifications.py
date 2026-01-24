from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from app.core.database import get_db
from app.schemas.notification import NotificationResponse, NotificationUpdate
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from typing import List

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notifications for current user"""
    query = select(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at))
    
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications of the current user as read"""
    query = update(Notification).filter(
        Notification.user_id == current_user.id
    ).values(is_read=True)
    
    await db.execute(query)
    await db.commit()
    return {"message": "All notifications marked as read"}

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_in: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read/unread"""
    query = select(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.id == notification_id
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if notification_in.is_read is not None:
        notification.is_read = notification_in.is_read
    
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

