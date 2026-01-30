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
        error_msg = str(e)
        print(f"❌ [Detailed] Google Sync Error: {error_msg}")
        # Log more detail if it's a google-auth error
        if hasattr(e, 'response'):
            print(f"❌ Response body: {e.response.text}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google Auth Error: {error_msg}"
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

@router.get("/google/events")
async def list_google_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to list upcoming events from Google.
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    tomorrow = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z'
    events = await google_calendar_service.get_calendar_events(current_user, db, time_min=now, time_max=tomorrow)
    return {"events": events}
