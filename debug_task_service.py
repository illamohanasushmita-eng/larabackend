import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import AsyncSessionLocal
from app.services.task_service import get_daily_plan, create_new_task
from app.schemas.task import TaskCreate

async def debug_tasks():
    async with AsyncSessionLocal() as db:
        print("\n🔍 --- DEBUGGING TASK SERVICE ---")
        
        # 1. Create a dummy test task for '10 AM Today'
        # Emulate Voice Input: 10 AM IST today
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
        today_date = now_ist.date()
        
        # 10:00 AM IST on Today
        # We must create it exactly how the frontend/ai_service would
        # ai_service returns an ISO string. Pydantic parses it.
        # Let's manually construct the UTC time for 10 AM IST.
        # 10:00 IST = 04:30 UTC
        
        target_ist = datetime.combine(today_date, datetime.min.time()).replace(hour=10, minute=0)
        target_ist = target_ist.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
        
        print(f"🛠️ Creating Test Task: 'Debug Voice Task'")
        print(f"   Target IST: {target_ist}")
        
        # Create using service (which handles normalization)
        t_data = TaskCreate(
            title="Debug Voice Task", 
            due_date=target_ist, # Service expects this input
            type="task"
        )
        # Assuming user_id=1 exists
        try:
            created = await create_new_task(db, t_data, 1)
            print(f"✅ Created Task ID: {created.id}")
            print(f"   Stored Due Date (DB): {created.due_date} (should be approx 04:30 Z)")
        except Exception as e:
            print(f"❌ Creation failed: {e}")
            return

        print("\n🔍 --- FETCHING DAILY PLAN ---")
        # 2. Fetch Plan
        plan = await get_daily_plan(db, 1)
        
        print(f"📋 Plan Result:")
        print(f"   Total Count: {plan['total_count']}")
        print(f"   Sections: {[s['slot'] for s in plan['sections']]}")
        
        found = False
        for s in plan['sections']:
            for t in s['items']:
                if t.id == created.id:
                    print(f"✅ FOUND created task in slot: {s['slot']}")
                    print(f"   Task Time Display: {t.due_date}")
                    found = True
        
        if not found:
            print("❌ Created task NOT found in daily plan!")

if __name__ == "__main__":
    asyncio.run(debug_tasks())
