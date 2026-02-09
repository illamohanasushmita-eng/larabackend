import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def add_post_due_columns():
    """
    Add notified_30m_post column to the tasks table.
    """
    print("🔍 Updating database schema for post-due reminders...")
    
    async with engine.begin() as conn:
        try:
            print("➕ Attempting to add column 'notified_30m_post'...")
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN notified_30m_post BOOLEAN DEFAULT FALSE;"))
            print("✅ Column 'notified_30m_post' added successfully.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("ℹ️ Column 'notified_30m_post' already exists, skipping.")
            else:
                print(f"⚠️ Error adding column: {e}")

    print("✨ Database update complete!")

if __name__ == "__main__":
    asyncio.run(add_post_due_columns())
