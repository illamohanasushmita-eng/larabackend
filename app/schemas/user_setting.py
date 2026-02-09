from pydantic import BaseModel
from typing import Optional

class UserSettingBase(BaseModel):
    morning_enabled: bool = True
    morning_time: str = "08:00"
    evening_enabled: bool = True
    evening_time: str = "21:00"
    push_enabled: bool = False
    fcm_token: Optional[str] = None

class UserSettingUpdate(BaseModel):
    morning_enabled: Optional[bool] = None
    morning_time: Optional[str] = None
    evening_enabled: Optional[bool] = None
    evening_time: Optional[str] = None
    push_enabled: Optional[bool] = None
    fcm_token: Optional[str] = None

class UserSettingResponse(UserSettingBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
