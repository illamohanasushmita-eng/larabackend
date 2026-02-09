import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def add_end_time_column():
    """
    Add end_time column to the tasks table.
    """
    print("🔍 Adding end_time column...")
    
    async with engine.begin() as conn:
        try:
            print("➕ Attempting to add column 'end_time'...")
            # Using TIMESTAMP WITH TIME ZONE to match due_date
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN end_time TIMESTAMP WITH TIME ZONE;"))
            print("✅ Column 'end_time' added successfully.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("ℹ️ Column 'end_time' already exists, skipping.")
            else:
                print(f"⚠️ Error adding column: {e}")

    print("✨ Database update complete!")

if __name__ == "__main__":
    asyncio.run(add_end_time_column())
