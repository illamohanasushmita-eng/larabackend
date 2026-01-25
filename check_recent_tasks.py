import asyncio
from app.core.database import async_session_maker
from app.models.task import Task
from sqlalchemy import select, desc
from datetime import datetime, timezone

async def check_tasks():
    async with async_session_maker() as session:
        # Get the 5 most recent tasks
        query = select(Task).order_by(desc(Task.created_at)).limit(5)
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        print("\n📋 Last 5 Tasks Created:")
        print("=" * 80)
        
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. ID: {task.id}")
            print(f"   Title: {task.title}")
            print(f"   Type: {task.type}")
            print(f"   User ID: {task.user_id}")
            print(f"   Due Date (DB/UTC): {task.due_date}")
            
            # Convert to IST for display
            if task.due_date:
                if task.due_date.tzinfo:
                    ist_time = task.due_date.astimezone(timezone.utc)
                else:
                    ist_time = task.due_date
                print(f"   Due Date (IST): {ist_time}")
            
            print(f"   Created At: {task.created_at}")
            print(f"   Status: {task.status}")

if __name__ == "__main__":
    asyncio.run(check_tasks())
