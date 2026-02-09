import asyncio
import sys
import os
sys.path.append('.')

from app.core.database import engine, Base
from app.models.task import Task

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_tables())
    print("Database tables created successfully!")
