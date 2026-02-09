import asyncio
from sqlalchemy import text
from app.core.database import engine

async def add_column():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE user_settings ADD COLUMN push_enabled BOOLEAN DEFAULT FALSE"))
            print("Successfully added push_enabled column to user_settings table.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column push_enabled already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    asyncio.run(add_column())
