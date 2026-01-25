from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

async def create_new_task(db: AsyncSession, task: TaskCreate, user_id: int):
    db_task = Task(
        title=task.title,
        raw_text=task.raw_text,
        description=task.description,
        due_date=task.due_date,
        type=task.type,
        user_id=user_id
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def get_tasks(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Task).filter(Task.user_id == user_id).offset(skip).limit(limit))
    return result.scalars().all()

async def get_task(db: AsyncSession, task_id: int, user_id: int):
    result = await db.execute(select(Task).filter(Task.id == task_id, Task.user_id == user_id))
    return result.scalars().first()

async def update_task_status(db: AsyncSession, task_id: int, task_update: TaskUpdate, user_id: int):
    db_task = await get_task(db, task_id, user_id)
    if not db_task:
        return None
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def get_daily_plan(db: AsyncSession, user_id: int, date_str: str = None):
    from datetime import date, datetime, time
    import random
    from app.models.user import User
    
    # Fetch user for name
    user_res = await db.execute(select(User).filter(User.id == user_id))
    user = user_res.scalar_one_or_none()
    user_name = user.full_name if user else "Friend"
    
    # Determine Greeting based on current time
    # ✅ Fix: Railway server is UTC, so we add 5:30 for IST (User's timezone)
    from datetime import timedelta
    now_ist = datetime.now() + timedelta(hours=5, minutes=30)
    now_hour = now_ist.hour
    
    if 5 <= now_hour < 12:
        greeting_time = "Good Morning"
    elif 12 <= now_hour < 17:
        greeting_time = "Good Afternoon"
    elif 17 <= now_hour < 21:
        greeting_time = "Good Evening"
    else:
        greeting_time = "Good Night"

    target_date = date.fromisoformat(date_str) if date_str else date.today()
    
    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date, time.max)
    
    query = select(Task).filter(
        Task.user_id == user_id,
        Task.due_date >= start_dt,
        Task.due_date <= end_dt
    ).order_by(Task.due_date)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "morning_message": f"{greeting_time}! 🙂 Your schedule is looking nice and light today.",
            "user_name": user_name,
            "sections": [],
            "total_count": 0,
            "time_bound_count": 0
        }
    
    sections_map = {
        "Morning": [],
        "Afternoon": [],
        "Evening": [],
        "Night": [],
        "Unscheduled": []
    }
    
    time_bound_count = 0
    for t in tasks:
        if not t.due_date:
            sections_map["Unscheduled"].append(t)
            continue
            
        time_bound_count += 1
        h = t.due_date.hour
        if 5 <= h < 12:
            sections_map["Morning"].append(t)
        elif 12 <= h < 16:
            sections_map["Afternoon"].append(t)
        elif 16 <= h < 20:
            sections_map["Evening"].append(t)
        else:
            sections_map["Night"].append(t)
            
    sections = [{"slot": k, "items": v} for k, v in sections_map.items() if v]
    
    count = len(tasks)
    if count == 1:
        msg = f"{greeting_time}! You have 1 task today. Let's make it count!"
    else:
        msg = f"{greeting_time}! You have {count} tasks scheduled. {time_bound_count} are time-sensitive."

    return {
        "morning_message": msg,
        "user_name": user_name,
        "sections": sections,
        "total_count": count,
        "time_bound_count": time_bound_count
    }

async def get_end_of_day_summary(db: AsyncSession, user_id: int):
    from datetime import date, datetime, time
    
    today = date.today()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today, time.max)
    
    # Fetch all tasks for today
    query = select(Task).filter(
        Task.user_id == user_id,
        Task.due_date >= start_dt,
        Task.due_date <= end_dt
    )
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    completed = [t for t in tasks if t.status == "completed"]
    pending = [t for t in tasks if t.status != "completed"]
    
    comp_count = len(completed)
    pend_count = len(pending)
    total = len(tasks)
    
    if total == 0:
        msg = "A quiet day! No tasks were scheduled today. Enjoy your evening!"
    elif pend_count == 0:
        msg = f"Fantastic! You crushed all {total} tasks today. Time to celebrate and rest!"
    elif comp_count > 0:
        msg = f"Good job! You completed {comp_count} out of {total} tasks. {pend_count} are still pending, but you made great progress!"
    else:
        msg = f"Today was tough! {total} tasks are still pending. Tomorrow is a fresh start to get things done!"

    return {
        "completed_count": comp_count,
        "pending_count": pend_count,
        "message": msg,
        "pending_items": pending
    }

async def get_user_insights(db: AsyncSession, user_id: int):
    """
    Calculate productivity metrics for the Insights screen
    """
    from datetime import datetime
    
    # helper for percentage
    def get_pct(part, whole):
        return int((part / whole) * 100) if whole > 0 else 0

    # 1. Total Tasks
    result = await db.execute(select(Task).filter(Task.user_id == user_id))
    all_tasks = result.scalars().all()
    
    total = len(all_tasks)
    completed = len([t for t in all_tasks if t.status == 'completed'])
    pending = len([t for t in all_tasks if t.status == 'pending'])
    
    # 2. Overdue Check
    now = datetime.now()
    overdue = 0
    for t in all_tasks:
        if t.status == 'pending' and t.due_date and t.due_date < now:
            overdue += 1
            
    completion_rate = get_pct(completed, total)
    
    # 3. Simple productivity score (arbitrary logic for fun)
    # Score = (Completion Rate * 0.7) + (Tasks Done * 2) - (Overdue * 5)
    # Capped at 100? No, let it be an XP points style
    score = (completion_rate * 5) + (completed * 10) - (overdue * 20)
    if score < 0: score = 0
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "overdue_tasks": overdue,
        "completion_rate": completion_rate,
        "productivity_score": score
    }

    from app.models.notification import Notification
    
    db_task = await get_task(db, task_id, user_id)
    if not db_task:
        return None
    
    # 🧹 Also delete related notifications from Inbox
    # We match by task_id in the JSON data column
    # Since JSON matching varies by DB, we rely on fetching and filtering or simple string match if safe
    # Or better: Add a task_id column to notifications? 
    # For now, let's delete strictly based on the stored data payload
    
    # Efficient approach: Select all notifs for this user, check data['task_id']
    # But filtering in memory is slow. 
    # Let's rely on cascading deletes if we had a foreign key, but we don't on Notification table for task_id (it's in JSON)
    
    # Alternative: Select notifications where user_id matches and filter in python
    # Ideally, we should update Notification model to have task_id.
    # For now, we will perform a safe cleanup:
    
    # Fetch user's notifications
    notifs_query = select(Notification).filter(Notification.user_id == user_id)
    n_res = await db.execute(notifs_query)
    all_notifs = n_res.scalars().all()
    
    for n in all_notifs:
        if n.data and n.data.get("task_id") == str(task_id):
            await db.delete(n)
    
    await db.delete(db_task)
    await db.commit()
    return db_task
