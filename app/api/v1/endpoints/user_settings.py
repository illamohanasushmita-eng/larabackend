from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user_setting import UserSettingResponse, UserSettingUpdate
from app.services import user_setting_service

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=UserSettingResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await user_setting_service.get_user_settings(db, current_user.id)

@router.put("/", response_model=UserSettingResponse)
async def update_settings(
    settings: UserSettingUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ✅ Fix: Capture ID before any awaits to avoid object expiration
    user_id = current_user.id
    updated_settings = await user_setting_service.update_user_settings(db, settings, user_id)
    
    # 🚀 If FCM token was just updated (synced from app), check if we should send a delayed Welcome Push
    if settings.fcm_token:
        # Check if they have a welcome notification recorded
        from sqlalchemy import select, and_
        from app.models.notification import Notification
        from app.core.fcm_manager import fcm_manager
        from app.services.notification_service import record_notification
        
        # Simple check: Do they have ANY notification of type 'welcome'?
        # We use user_id variable here
        query = select(Notification).filter(and_(Notification.user_id == user_id, Notification.data['type'].astext == 'welcome'))
        result = await db.execute(query)
        existing_welcome = result.scalars().first()
        
        if not existing_welcome:
            print(f"👋 [Welcome] Sending first-time welcome push to {current_user.email}")
            title = "Welcome to LARA! 🚀"
            body = "I'm here to assist you. Tap to explore!"
            
            # Send Push
            await fcm_manager.send_notification(
                token=settings.fcm_token,
                title=title,
                body=body,
                data={"type": "welcome"}
            )
            # Record it so we don't send again
            await record_notification(db, user_id, title, body, {"type": "welcome"})
            
    return updated_settings
