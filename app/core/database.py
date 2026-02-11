from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import sys

# 1. Fetch the Database URL from settings (which pulls from .env)
DATABASE_URL = settings.DATABASE_URL

# 2. Validation: Ensure DATABASE_URL is present
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL is not set in the environment or .env file.")
    print("Please add DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname to your .env")
    # For a FastAPI app, raising an error here prevents the app from starting in a broken state
    raise ValueError("DATABASE_URL must be set in the environment variables.")

# 3. Supabase/Heroku Fix: 
# Supabase provides 'postgresql://'. Async SQLAlchemy requires 'postgresql+asyncpg://'
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    # Heroku style
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# 4. Create the Async Engine
# connect_args={"ssl": True} or sslmode in string is required for Supabase Production
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # Supabase best practice for Async components
    connect_args={"ssl": "require"} if "localhost" not in DATABASE_URL else {},
    pool_pre_ping=True,  # 🟢 FIX: Check connection health before using
    pool_recycle=300     # 🟢 FIX: Recycle connections every 5 mins to avoid timeouts
)

# 5. Create Session Factory
# We name it AsyncSessionLocal to distinguish from the standard sync SessionLocal
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False
)

# 6. Base class for Models
Base = declarative_base()

# 7. Dependency for FastAPI endpoints
async def get_db():
    """
    FastAPI dependency that provides a safe database session for each request.
    Automatically closes the session after the request is finished.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

