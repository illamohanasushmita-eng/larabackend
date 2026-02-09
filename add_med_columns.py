import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def add_medicine_columns():
    """
    Add med_timing column to the tasks table.
    """
    print("🔍 Adding medicine-specific columns...")
    
    async with engine.begin() as conn:
        try:
            print("➕ Attempting to add column 'med_timing'...")
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN med_timing VARCHAR;"))
            print("✅ Column 'med_timing' added successfully.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("ℹ️ Column 'med_timing' already exists, skipping.")
            else:
                print(f"⚠️ Error adding column: {e}")

    print("✨ Database update complete!")

if __name__ == "__main__":
    asyncio.run(add_medicine_columns())
