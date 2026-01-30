from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password

async def create_user(db: AsyncSession, user_in: UserCreate):
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email.lower().strip(),
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email.lower().strip()))
    return result.scalars().first()

async def update_user_profile(db: AsyncSession, user_id: int, user_update: dict):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    if db_user:
        for key, value in user_update.items():
            if hasattr(db_user, key):
                setattr(db_user, key, value)
        await db.commit()
        await db.refresh(db_user)
    return db_user

async def handle_google_login(db: AsyncSession, email: str, full_name: str = None):
    # Try to find user
    user = await get_user_by_email(db, email)
    if not user:
        # Create new user for Google login
        user = User(
            email=email.lower().strip(),
            full_name=full_name,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create welcome notification
        try:
            from app.models.notification import Notification
            welcome_notif = Notification(
                user_id=user.id,
                title="Google Login Successful! 🚀",
                body="Welcome to LARA. We've set up your account via Google.",
                data={"type": "welcome"}
            )
            db.add(welcome_notif)
            await db.commit()
        except Exception as e:
            print(f"⚠️ Failed to create welcome notification: {e}")
            
    return user
