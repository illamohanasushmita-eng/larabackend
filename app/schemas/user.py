from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    profession: Optional[str] = None

class UserCreate(UserBase):
    email: str
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool

    @property
    def onboarding_completed(self) -> bool:
        # User is considered onboarded if they have set their profession (last step of onboarding)
        return bool(self.profession)

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: Optional[str] = None
    server_auth_code: Optional[str] = None
    email: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    onboarding_completed: bool = False

class TokenData(BaseModel):
    sub: Optional[str] = None
