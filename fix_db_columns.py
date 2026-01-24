import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def fix_database_schema():
    """
    Manually add missing columns to the tasks table for PostgreSQL/SQLite.
    This fixes the 'column tasks.raw_text does not exist' error.
    """
    print("🔍 Checking and fixing database schema...")
    
    async with engine.begin() as conn:
        # Columns to add
        columns_to_add = [
            ("raw_text", "VARCHAR"),
            ("notified_10m", "BOOLEAN DEFAULT FALSE"),
            ("notified_20m", "BOOLEAN DEFAULT FALSE")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                print(f"➕ Attempting to add column '{col_name}'...")
                # Note: 'IF NOT EXISTS' is not supported in 'ALTER TABLE ADD COLUMN' for all DBs 
                # so we use a try-except block
                await conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type};"))
                print(f"✅ Column '{col_name}' added successfully.")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"ℹ️ Column '{col_name}' already exists, skipping.")
                else:
                    print(f"⚠️ Error adding column '{col_name}': {e}")

    print("✨ Database schema fix complete!")

if __name__ == "__main__":
    asyncio.run(fix_database_schema())
