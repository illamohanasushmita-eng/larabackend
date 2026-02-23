from fastapi import APIRouter
from app.api.v1.endpoints import tasks, user_settings, notifications, users, ai, calendar, places

api_router = APIRouter()
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(user_settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
