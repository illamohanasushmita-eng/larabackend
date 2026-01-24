
import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal, engine

async def check_schema():
    async with engine.connect() as conn:
        print("Checking tasks table:")
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tasks'"))
        for row in result:
            print(row)
            
        print("\nChecking user_settings table:")
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'user_settings'"))
        for row in result:
            print(row)

if __name__ == "__main__":
    asyncio.run(check_schema())
