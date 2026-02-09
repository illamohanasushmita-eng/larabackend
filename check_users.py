
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_users():
    async with engine.connect() as conn:
        print("\n--- Users Table ---")
        result = await conn.execute(text("SELECT id, email FROM users"))
        for row in result:
            print(row)
            
        print("\n--- User Settings Table ---")
        result = await conn.execute(text("SELECT id, user_id FROM user_settings"))
        for row in result:
            print(row)

if __name__ == "__main__":
    asyncio.run(check_users())
