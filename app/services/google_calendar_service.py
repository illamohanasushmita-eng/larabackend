import os
import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.config import settings

# Path to the credentials file you uploaded
CLIENT_SECRET_FILE = "client_secret.json"

async def exchange_code_for_tokens(db: AsyncSession, user: User, code: str):
    """
    Exchange authorization code for access and refresh tokens.
    """
    # Use config from env instead of file to avoid project mismatches
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar.events'
        ],
        redirect_uri='https://web-production-6ff602.up.railway.app/api/v1/calendar/google/sync'
    )

    # Exchange code
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Update user in database
    user.google_access_token = credentials.token
    if credentials.refresh_token:
        user.google_refresh_token = credentials.refresh_token
    user.google_token_expiry = credentials.expiry

    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

async def get_calendar_events(user: User, db: AsyncSession, time_min: str = None, time_max: str = None):
    """
    Fetch events from Google Calendar with automatic token refreshing.
    """
    if not user.google_refresh_token:
        print("ℹ️ No Google refresh token found for user.")
        return []

    import google.oauth2.credentials
    from google.auth.transport.requests import Request

    creds = google.oauth2.credentials.Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/calendar.events']
    )

    try:
        # 🔄 Refresh token if expired
        if creds.expired:
            print("🔄 Google Access Token expired, refreshing...")
            creds.refresh(Request())
            
            # Save the new tokens to the database
            user.google_access_token = creds.token
            if creds.refresh_token:
                user.google_refresh_token = creds.refresh_token
            user.google_token_expiry = creds.expiry
            
            db.add(user)
            await db.commit()
            print("✅ Tokens refreshed and saved successfully.")

        service = build('calendar', 'v3', credentials=creds)
        
        if not time_min:
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'
        if not time_max:
            time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z'

        print(f"📅 Fetching events from {time_min} to {time_max}")

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Google API returned {len(events)} events.")
        return events
        
    except Exception as e:
        print(f"❌ Google API Error in get_calendar_events: {e}")
        return []
