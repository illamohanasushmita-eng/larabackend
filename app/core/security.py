from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_truncate_password(plain_password), hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(_truncate_password(password))

def _truncate_password(password: str) -> str:
    """
    Bcrypt has a 72-byte limit. We truncate the password safely
    to stay within this limit if it's too long.
    """
    if not password:
        return ""
    
    # Encode to bytes to check the actual byte length
    pw_bytes = password.encode("utf-8")
    
    if len(pw_bytes) > 72:
        # Truncate to 72 bytes and decode back safely (ignoring partial chars)
        return pw_bytes[:72].decode("utf-8", errors="ignore")
    
    return password
