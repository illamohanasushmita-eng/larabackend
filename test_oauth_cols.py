import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def test_insert():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    print(f"Testing insert to: {url.split('@')[-1]}")
    try:
        conn = await asyncpg.connect(url)
        # Try to update a user (or just select the columns)
        row = await conn.fetchrow("SELECT id, google_access_token FROM users LIMIT 1;")
        if row:
            print(f"Success! Found user {row['id']} with token {row['google_access_token']}")
        else:
            print("No users found, but query worked!")
        await conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_insert())
