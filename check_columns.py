import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def check_columns():
    async with engine.connect() as conn:
        try:
            # Check for Postgres
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks';"))
            columns = [row[0] for row in result.fetchall()]
            print(f"Current columns in 'tasks' table: {columns}")
        except Exception as e:
            print(f"Error checking columns: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())
