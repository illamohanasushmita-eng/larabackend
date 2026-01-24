from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, UserUpdate
from app.services import user_service
from app.core import security
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=Token)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_email(db, user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    new_user = await user_service.create_user(db, user_in)
    
    # 🚀 Send Welcome Notification
    try:
        from app.core.fcm_manager import fcm_manager
        # We need the user's token, but new users might not have one yet until they login on the app.
        # Wait, the token comes from the frontend AFTER login.
        # So we can't send a push *immediately* here because we don't have the FCM token in DB yet.
        # The token is saved in /update_settings usually.
        
        # Correction: We can't push here. We should do it when the token is first synced?
        # OR: We can just create an Inbox notification record so they see it when they open the notifications screen.
        
        from app.models.notification import Notification
        welcome_notif = Notification(
            user_id=new_user.id,
            title="Welcome to LARA! 🚀",
            body="I'm here to help you organize your life. Try adding your first task!",
            data={"type": "welcome"}
        )
        db.add(welcome_notif)
        await db.commit()
    except Exception as e:
        print(f"⚠️ Failed to create welcome notification: {e}")
        
    # Auto-login after registration
    access_token = security.create_access_token(new_user.id)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "onboarding_completed": False # Always false for new registration
    }

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_email(db, user_in.email)
    
    is_verified = False
    if user:
        try:
            is_verified = user_service.verify_password(user_in.password, user.hashed_password)
        except Exception as e:
            # Handle UnknownHashError or other passlib/bcrypt issues gracefully
            print(f"⚠️ [Login] Password verification failed for {user_in.email}: {str(e)}")
            is_verified = False

    if not user or not is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(user.id)
    
    # Check if onboarding is complete (profession is the last field)
    onboarding_done = bool(user.profession)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "onboarding_completed": onboarding_done
    }


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Pass current_user.id to ensure security
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await user_service.update_user_profile(db, current_user.id, update_data)
    return updated_user
