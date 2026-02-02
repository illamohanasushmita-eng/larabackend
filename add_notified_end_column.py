import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def add_notified_end_column():
    """
    Add notified_end column to the tasks table.
    """
    print("🔍 Adding notified_end column...")
    
    async with engine.begin() as conn:
        try:
            print("➕ Attempting to add column 'notified_end'...")
            # Boolean column for tracking the end notification
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN notified_end BOOLEAN DEFAULT FALSE;"))
            print("✅ Column 'notified_end' added successfully.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("ℹ️ Column 'notified_end' already exists, skipping.")
            else:
                print(f"⚠️ Error adding column: {e}")

    print("✨ Database update complete!")

if __name__ == "__main__":
    asyncio.run(add_notified_end_column())
