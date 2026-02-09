import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def check_db():
    print("🔍 Checking database for notifications...")
    async with engine.connect() as conn:
        # Check tables
        res = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"))
        tables = [r[0] for r in res.fetchall()]
        print(f"📊 Tables found: {tables}")
        
        if 'notifications' in tables:
            res = await conn.execute(text("SELECT count(*) FROM notifications"))
            count = res.scalar()
            print(f"📈 Total Notifications in DB: {count}")
            
            if count > 0:
                res = await conn.execute(text("SELECT id, user_id, title FROM notifications LIMIT 5"))
                for row in res.fetchall():
                    print(f"  - ID: {row[0]}, User: {row[1]}, Title: {row[2]}")
        else:
            print("❌ Table 'notifications' does not exist!")

if __name__ == "__main__":
    asyncio.run(check_db())
