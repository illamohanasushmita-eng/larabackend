import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def delete_tasks():
    print("Starting delete...", flush=True)
    with open("delete_status.txt", "w") as f:
        f.write("Starting...\n")
    
    try:
        async with engine.begin() as conn:
            res = await conn.execute(text("SELECT count(*) FROM tasks"))
            count = res.scalar()
            
            await conn.execute(text("DELETE FROM tasks"))
            
            print(f"Deleted {count} tasks.", flush=True)
            with open("delete_status.txt", "a") as f:
                f.write(f"Deleted {count} tasks.\nDone.")
    except Exception as e:
        print(f"Error: {e}", flush=True)
        with open("delete_status.txt", "a") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(delete_tasks())
