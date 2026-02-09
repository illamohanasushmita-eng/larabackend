import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_columns():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    print(f"Checking database: {url.split('@')[-1]}") # Log host only for safety
    try:
        conn = await asyncpg.connect(url)
        rows = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        columns = [r['column_name'] for r in rows]
        print("Columns in 'users' table:")
        for col in columns:
            print(f" - {col}")
            
        required = ['google_access_token', 'google_refresh_token', 'google_token_expiry']
        missing = [col for col in required if col not in columns]
        
        if not missing:
            print("\n✅ All Google OAuth columns exist!")
        else:
            print(f"\n❌ Missing columns: {missing}")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())
