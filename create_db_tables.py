import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, Base
from app.models.task import Task
from app.models.user_setting import UserSetting

async def create_tables():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

    # Verify tables were created
    print("Verifying tables...")
    async with engine.begin() as conn:
        try:
            # Try SQLite first
            result = await conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = result.fetchall()
            print(f"Created (SQLite) tables: {[table[0] for table in tables]}")
        except:
            # Fallback for Postgres
            try:
                result = await conn.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';")
                tables = result.fetchall()
                print(f"Created (Postgres) tables: {[table[0] for table in tables]}")
            except Exception as e:
                print(f"Could not verify tables details, but metadata check passed. Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())
