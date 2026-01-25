import asyncio
from app.core.database import async_session_maker
from app.models.task import Task
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone

async def fix_offsets():
    async with async_session_maker() as session:
        # 1. Find tasks that were potentially saved with incorrect naive-UTC offsets
        # If a task was created recently and has a due_date that looks like an un-normalized IST time
        # (e.g., it's later in the UTC day than the current IST day ends)
        
        # Actually, let's just find all tasks for Today/Tomorrow and see if any are clearly "voice tasks with bad offsets"
        query = select(Task).where(Task.due_date >= datetime.now() - timedelta(days=1))
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        print(f"🔍 Analyzing {len(tasks)} recent tasks...")
        
        fixed_count = 0
        for task in tasks:
            # Heuristic: If it was saved naive-UTC but logically belongs to Today IST, it might be shifted
            # Specifically, if it falls between 18:30 UTC and 23:59 UTC on the same calendar day, 
            # it was likely meant to be IST (so it should have been subtracted by 5:30)
            
            h = task.due_date.hour
            m = task.due_date.minute
            
            # If time is between 18:30 and 23:59 UTC
            # It's highly likely it was an IST timestamp saved as UTC
            if (h > 18) or (h == 18 and m >= 30):
                new_due_date = task.due_date - timedelta(hours=5, minutes=30)
                print(f"🩹 Fixing Task {task.id}: '{task.title}'")
                print(f"   Old: {task.due_date} UTC")
                print(f"   New: {new_due_date} UTC (Corrected IST->UTC shift)")
                
                task.due_date = new_due_date
                fixed_count += 1
        
        if fixed_count > 0:
            await session.commit()
            print(f"✅ Successfully corrected {fixed_count} task offsets.")
        else:
            print("✨ No problematic offsets found.")

if __name__ == "__main__":
    asyncio.run(fix_offsets())
