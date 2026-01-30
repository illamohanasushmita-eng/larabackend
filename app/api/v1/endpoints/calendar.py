from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.google import GoogleAuthCode, GoogleSyncStatus
from app.services import google_calendar_service

router = APIRouter()

@router.post("/google/sync", response_model=GoogleSyncStatus)
async def sync_google_calendar(
    auth_data: GoogleAuthCode,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint to receive the auth code from the mobile app and sync Google Calendar.
    """
    try:
        updated_user = await google_calendar_service.exchange_code_for_tokens(
            db, current_user, auth_data.code
        )
        return {
            "is_synced": True,
            "email": current_user.email
        }
    except Exception as e:
        print(f"❌ Google Sync Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to sync with Google: {str(e)}"
        )

@router.get("/google/status", response_model=GoogleSyncStatus)
async def get_google_sync_status(current_user: User = Depends(get_current_user)):
    """
    Check if the user has already synced their Google account.
    """
    return {
        "is_synced": bool(current_user.google_refresh_token),
        "email": current_user.email if current_user.google_refresh_token else None
    }
