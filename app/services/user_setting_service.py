from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_setting import UserSetting
from app.schemas.user_setting import UserSettingUpdate

async def get_user_settings(db: AsyncSession, user_id: int):
    # Debug log to catch where 'default_user' is coming from
    print(f"🔍 [get_user_settings] Received user_id: {user_id} (type: {type(user_id)})")
    
    # Ensure user_id is int to avoid 'integer = character varying' errors
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        print(f"❌ [get_user_settings] FAILED to convert user_id '{user_id}' to int")
        raise ValueError(f"Invalid user_id type: {type(user_id)}. Value: {user_id}. Expected integer string or int.")

    query = select(UserSetting).filter(UserSetting.user_id == user_id_int)
    print(f"📝 [get_user_settings] Executing query: {query}")
    result = await db.execute(query)
    settings = result.scalars().first()
    
    if not settings:
        # Create default if not exists
        settings = UserSetting(user_id=user_id_int)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    return settings

async def update_user_settings(db: AsyncSession, settings_update: UserSettingUpdate, user_id: int):
    settings = await get_user_settings(db, user_id)
    
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings
