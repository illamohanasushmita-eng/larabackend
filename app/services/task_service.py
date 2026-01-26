from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

async def create_new_task(db: AsyncSession, task: TaskCreate, user_id: int):
    import logging
    from datetime import timezone, timedelta
    import pytz
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"📝 Creating task for user {user_id}")
    logger.info(f"   Title: {task.title}")
    logger.info(f"   Due Date: {task.due_date}")
    logger.info(f"   Type: {task.type}")
    
    try:
        # 🕒 Timezone Normalization Fix
        # If the task has a due_date, ensure it's converted to UTC before saving.
        # FIX: Treat Naive as IST because users are likely sending local time from an app acting in IST
        # If we treat naive as UTC, a 9 PM task becomes 9 PM UTC = 2:30 AM IST (Next Day), causing it to disappear from 'Today'.
        
        normalized_due_date = task.due_date
        if normalized_due_date:
            if normalized_due_date.tzinfo is not None:
                # Convert Aware to UTC
                normalized_due_date = normalized_due_date.astimezone(timezone.utc)
            else:
                # Treat Naive as IST (Asia/Kolkata)
                ist_tz = pytz.timezone('Asia/Kolkata')
                # Localize as IST
                dt_ist = ist_tz.localize(normalized_due_date)
                # Convert to UTC
                normalized_due_date = dt_ist.astimezone(timezone.utc)
                
            logger.info(f"🔄 Normalized due_date to Aware UTC: {normalized_due_date}")

        # Normalize Type and Status
        safe_type = task.type.lower() if task.type else "task"
        if safe_type not in ["task", "reminder", "meeting"]:
            safe_type = "task"
            
        db_task = Task(
            title=task.title,
            raw_text=task.raw_text,
            description=task.description,
            due_date=normalized_due_date,
            type=safe_type,
            status="pending", # Force default status
            user_id=user_id
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        logger.info(f"✅ Task created successfully! ID: {db_task.id}")
        return db_task
    except Exception as e:
        logger.error(f"❌ Failed to create task: {e}")
        await db.rollback()
        raise

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
    # Determine Greeting based on current time
    # ✅ Fix: Railway server is UTC, so we add 5:30 for IST (User's timezone)
    from datetime import timedelta, timezone
    import logging
    logger = logging.getLogger(__name__)
    
    # Use explicit UTC now to avoid local system time ambiguity
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
    now_hour = now_ist.hour
    
    if 5 <= now_hour < 12:
        greeting_time = "Good Morning"
    elif 12 <= now_hour < 17:
        greeting_time = "Good Afternoon"
    elif 17 <= now_hour < 21:
        greeting_time = "Good Evening"
    else:
        greeting_time = "Good Night"

    # ✅ CRITICAL FIX: Use IST date, not server UTC date
    # If date_str is provided, use it. Otherwise, use TODAY in IST.
    if date_str:
        target_date = date.fromisoformat(date_str)
    else:
        # Server is in UTC, but user expects "today" in IST
        target_date = now_ist.date()
    
    logger.info(f"📅 [get_daily_plan] Target date: {target_date} (IST)")
    
    # 🌍 Fix: Handle Timezone properly.
    # Postgres stores UTC. We construct Aware UTC ranges to query.
    # from datetime import timezone # already imported
    
    # 1. Create 00:00 IST on target date (naive)
    dt_ist_start = datetime.combine(target_date, time.min) # 00:00:00
    dt_ist_end = datetime.combine(target_date, time.max)   # 23:59:59.999
    
    # 2. Convert IST target range to Aware UTC range
    # IST = UTC + 5:30. To get UTC, we subtract 5:30 and tag as UTC.
    dt_utc_start = (dt_ist_start - timedelta(hours=5, minutes=30)).replace(tzinfo=timezone.utc)
    dt_utc_end = (dt_ist_end - timedelta(hours=5, minutes=30)).replace(tzinfo=timezone.utc)
    
    logger.info(f"🔍 [get_daily_plan] IST window: {dt_ist_start} to {dt_ist_end}")
    logger.info(f"🔍 [get_daily_plan] UTC window (Aware): {dt_utc_start} to {dt_utc_end}")
    
    # Fetch tasks with a wider buffer (±1 Day) to ensure we catch everything despite timezone shifts
    # Then filter strictly in Python
    buffer = timedelta(days=1)
    query_start = dt_utc_start - buffer
    query_end = dt_utc_end + buffer
    
    query = select(Task).filter(
        Task.user_id == user_id,
        Task.due_date >= query_start,
        Task.due_date <= query_end
    ).order_by(Task.due_date)
    
    result = await db.execute(query)
    all_potential_tasks = result.scalars().all()
    
    # Strict Python Filter for "Today" in IST
    tasks = []
    logger.info(f"📊 [get_daily_plan] Filtering {len(all_potential_tasks)} candidates for {target_date}")
    
    for t in all_potential_tasks:
        if not t.due_date:
            continue
            
        # Convert DB time to IST
        # Handle naive as UTC
        t_utc = t.due_date
        if t_utc.tzinfo is None:
            t_utc = t_utc.replace(tzinfo=timezone.utc)
            
        t_ist = t_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
        
        if t_ist.date() == target_date:
            tasks.append(t)
        else:
            # logger.info(f"   Skipping {t.title} at {t_ist} (Date mismatch)")
            pass
            
    # Include unscheduled tasks if any (though usually they have no date, handled separately?)
    # If due_date is None, our SQL filter ^ skips them unless we allow None
    # Let's separately fetch unscheduled if needed, but 'get_daily_plan' usually implies scheduled.
    # Actually, current SQL `Task.due_date >= ...` excludes Nulls automatically.
    # We should add `OR Task.due_date IS NULL` if we want unscheduled.
    # But usually Daily Plan is time-focused.
    
    # Re-apply sorting
    tasks.sort(key=lambda x: x.due_date)
    
    # 🕵️ Debug: Check if any tasks were excluded that might have been today
    all_query = select(Task).filter(Task.user_id == user_id).limit(20)
    all_res = await db.execute(all_query)
    all_tasks = all_res.scalars().all()
    
    logger.info(f"📊 [get_daily_plan] Found {len(tasks)} tasks in window. User total tasks checked: {len(all_tasks)}")
    for t in all_tasks:
        if t.due_date:
            # Ensure comparison is done on aware UTC datetimes
            t_due = t.due_date
            if t_due.tzinfo is None:
                t_due = t_due.replace(tzinfo=timezone.utc)
            else:
                t_due = t_due.astimezone(timezone.utc)
            
            in_window = dt_utc_start <= t_due <= dt_utc_end
            if not in_window and t_due.date() == target_date:
                 logger.info(f"⚠️  Task excluded: ID={t.id}, Title='{t.title}', Due={t_due}")
    
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
        
        # 🕒 Convert UTC due_date to IST for grouping
        # due_date from DB is naive UTC (usually) or aware UTC
        dt_utc = t.due_date
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
            
        # Convert to IST
        # We manually shift by +5:30 for display logic grouping
        dt_ist = dt_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
        h = dt_ist.hour
        
        if 5 <= h < 12:
            sections_map["Morning"].append(t)
        elif 12 <= h < 16:
            sections_map["Afternoon"].append(t)
        elif 16 <= h < 20:
            sections_map["Evening"].append(t)
        else:
            sections_map["Night"].append(t)
            
    sections = [{"slot": k, "items": v} for k, v in sections_map.items() if len(v) > 0]
    
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
    from datetime import date, datetime, time, timedelta, timezone
    
    # Use UTC now converted to IST
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
    target_date = now_ist.date()
    
    # Define IST window in UTC
    dt_ist_start = datetime.combine(target_date, time.min)
    dt_ist_end = datetime.combine(target_date, time.max)
    
    dt_utc_start = (dt_ist_start - timedelta(hours=5, minutes=30)).replace(tzinfo=timezone.utc)
    dt_utc_end = (dt_ist_end - timedelta(hours=5, minutes=30)).replace(tzinfo=timezone.utc)
    
    # Fetch all tasks for today (UTC window)
    query = select(Task).filter(
        Task.user_id == user_id,
        Task.due_date >= dt_utc_start,
        Task.due_date <= dt_utc_end
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
