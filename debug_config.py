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
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "lara_db")
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"), case_sensitive=True, extra="ignore")

    def __init__(self, **data):
        super().__init__(**data)
        print(f"DATABASE_URL from env before init: {self.DATABASE_URL}")
        if not self.DATABASE_URL:
             self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        print(f"DATABASE_URL after init: {self.DATABASE_URL}")

settings = Settings()

print(f"Final DATABASE_URL: {settings.DATABASE_URL}")
print(f"Env vars: {dict(os.environ)}")
