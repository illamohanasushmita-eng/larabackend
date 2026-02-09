from pydantic import BaseModel
from typing import Optional

class GoogleAuthCode(BaseModel):
    code: str

class GoogleSyncStatus(BaseModel):
    is_synced: bool
    email: Optional[str] = None
