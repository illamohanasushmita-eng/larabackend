import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "LARA - AI Voice Assistant"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgre")  # Force correct username
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgre")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "lara_db")
    DATABASE_URL: str | None = None
    
    FIREBASE_CREDENTIALS: str = "firebase-service-account.json"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_me_in_prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"), case_sensitive=True, extra="ignore")

    def __init__(self, **data):
        super().__init__(**data)
        # Use PostgreSQL as requested
        if not self.DATABASE_URL:
             self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
