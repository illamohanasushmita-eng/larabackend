import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_columns_extended():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {url.split('@')[-1]}")
    try:
        conn = await asyncpg.connect(url)
        
        # Check current schema
        schema = await conn.fetchval("SELECT current_schema();")
        print(f"Current schema: {schema}")
        
        # List all tables in all schemas
        tables = await conn.fetch("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name = 'users';
        """)
        print("\nFound 'users' tables in these schemas:")
        for t in tables:
            print(f" - {t['table_schema']}.{t['table_name']}")
            
            # Check columns for this specific table
            cols = await conn.fetch(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{t['table_schema']}' 
                AND table_name = 'users';
            """)
            print(f"   Columns: {[c['column_name'] for c in cols]}")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns_extended())
