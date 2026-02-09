from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool = False

class NotificationCreate(BaseModel):
    title: str
    body: str
    data: Optional[dict] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
