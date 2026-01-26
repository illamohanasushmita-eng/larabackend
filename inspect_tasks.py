import asyncio
import sys
import os
from sqlalchemy import text
from app.core.database import engine

async def inspect_recent_tasks():
    print("\n🔍 --- INSPECTING RECENT TASKS ---")
    async with engine.connect() as conn:
        # Fetch last 5 tasks
        result = await conn.execute(text("SELECT id, title, due_date, type, status FROM tasks ORDER BY id DESC LIMIT 5"))
        tasks = result.fetchall()
        
        if not tasks:
            print("❌ No tasks found in DB.")
            return

        for t in tasks:
            t_id, title, due, t_type, status = t
            print(f"🆔 {t_id} | 📝 '{title}' | 🕒 {due} (Raw DB Value) | 🏷️ {t_type} | ❓ {status}")
            
            # timezone check
            if due:
                print(f"      ↳ TzInfo: {due.tzinfo}")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    asyncio.run(inspect_recent_tasks())
