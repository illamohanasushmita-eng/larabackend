import asyncio
from app.core.database import engine
from sqlalchemy import inspect

async def check_tables():
    print("Connecting to database to check tables...")
    try:
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            print(f"Existing tables in database: {tables}")
            if "tasks" in tables:
                print("✅ 'tasks' table exists.")
            else:
                print("❌ 'tasks' table DOES NOT exist.")
            
            if "user_settings" in tables:
                print("✅ 'user_settings' table exists.")
            else:
                print("❌ 'user_settings' table DOES NOT exist.")
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())
