import os
import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.config import settings

# Path to the credentials file you uploaded
CLIENT_SECRET_FILE = "client_secret.json"

# Single source of truth for scopes
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks.readonly'
]

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
        scopes=SCOPES,
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

async def get_google_data(user: User, db: AsyncSession, time_min: str = None, time_max: str = None):
    """
    Fetch both Events and Tasks from Google.
    """
    if not user.google_refresh_token:
        return {"events": [], "tasks": []}

    import google.oauth2.credentials
    from google.auth.transport.requests import Request

    # 1. Initialize Credentials WITHOUT enforcing scopes.
    # This prevents "invalid_scope" errors if the user's token hasn't been upgraded yet.
    # The refresh() call will just refresh whatever scopes were originally granted.
    creds = google.oauth2.credentials.Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET
        # DO NOT Pass scopes here, let the token dictate them.
    )

    try:
        if creds.expired:
            try:
                creds.refresh(Request())
                user.google_access_token = creds.token
                db.add(user)
                await db.commit()
            except Exception as refresh_err:
                 print(f"⚠️ Refresh failed: {refresh_err}")
                 # If refresh fails entirely, we can't proceed
                 return {"events": [], "tasks": []}

        # 1. Fetch Calendar Events (Assume this scope is always present for synced users)
        events = []
        try:
            cal_service = build('calendar', 'v3', credentials=creds)
            if not time_min:
                time_min = datetime.datetime.utcnow().isoformat() + 'Z'
            if not time_max:
                time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z'

            events_result = cal_service.events().list(
                calendarId='primary', timeMin=time_min, timeMax=time_max, singleEvents=True
            ).execute()
            events = events_result.get('items', [])
        except Exception as ce:
            print(f"⚠️ Calendar API error: {ce}")

        # 2. Fetch Google Tasks
        tasks = []
        # Dynamically check if our token has the tasks scope
        # Note: creds.scopes might be None immediately after init, but populated after refresh/use.
        # Alternatively, we just try-catch.
        
        has_tasks_scope = False
        if creds.scopes:
             if 'https://www.googleapis.com/auth/tasks.readonly' in creds.scopes:
                 has_tasks_scope = True
        else:
             # If scopes not populated, we can try optimistic, or assuming NO if not sure.
             # But 'google-auth' usually populates it on refresh. 
             # Let's simple Try-Catch block handle it, which is robust.
             has_tasks_scope = True 

        if has_tasks_scope:
            try:
                tasks_service = build('tasks', 'v1', credentials=creds)
                # 1. Get all task lists
                tasklists_result = tasks_service.tasklists().list().execute()
                tasklists = tasklists_result.get('items', [])
                
                # 2. Fetch tasks from each list
                for tl in tasklists:
                    t_res = tasks_service.tasks().list(tasklist=tl['id']).execute()
                    tasks.extend(t_res.get('items', []))
                    
            except Exception as te:
                if "403" in str(te) or "401" in str(te):
                    print(f"ℹ️ Tasks API skipped (Scope likely missing, user needs to re-sync).")
                else:
                    print(f"⚠️ Tasks API error: {te}")

        return {"events": events, "tasks": tasks}
        
    except Exception as e:
        print(f"❌ Google API Error: {e}")
        return {"events": [], "tasks": []}
