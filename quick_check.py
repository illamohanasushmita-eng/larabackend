
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    print("Connecting...")
    try:
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER", "postgre"),
            password=os.getenv("POSTGRES_PASSWORD", "postgre"),
            database=os.getenv("POSTGRES_DB", "lara_db"),
            host=os.getenv("POSTGRES_SERVER", "localhost")
        )
        print("Connected!")
        rows = await conn.fetch("SELECT id, email, hashed_password FROM users")
        for row in rows:
            hp = row['hashed_password']
            prefix = hp[:10] if hp else "NONE"
            print(f"User: {row['email']}, Hash: {prefix}...")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
