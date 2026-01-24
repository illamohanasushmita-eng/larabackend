
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def dump_db():
    async with engine.connect() as conn:
        print("\n--- USERS ---")
        res = await conn.execute(text("SELECT id, email, hashed_password FROM users"))
        for row in res:
            # Print just the start of the hash for privacy but enough to see the format
            hashed = str(row[2])
            format_check = hashed[:10] + "..." if len(hashed) > 10 else hashed
            print(f"ID: {row[0]}, Email: {row[1]}, Hash prefix: {format_check}")
            
        print("\n--- USER SETTINGS ---")
        res = await conn.execute(text("SELECT id, user_id FROM user_settings"))
        for row in res:
            print(row)

if __name__ == "__main__":
    asyncio.run(dump_db())
