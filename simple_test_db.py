import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    url = "postgresql+asyncpg://postgres:sgUGlibMrGpDHHIbADOCDwHCQzfnIqUz@ballast.proxy.rlwy.net:48465/railway"
    print(f"Connecting to {url}...")
    try:
        engine = create_async_engine(url, connect_args={"ssl": "require"})
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Result: {result.fetchone()}")
            
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks';"))
            cols = [r[0] for r in result.fetchall()]
            print(f"Columns: {cols}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
