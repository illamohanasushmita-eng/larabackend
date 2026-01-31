from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from app.models.task import Task
from app.models.user_setting import UserSetting
from app.models.notification import Notification
from app.core.fcm_manager import fcm_manager
import json
import random
import logging
from app.services.ai_service import generate_friendly_reminder
from app.models.user import User
from app.services import google_calendar_service

logger = logging.getLogger(__name__)

async def check_and_send_notifications(db: AsyncSession):
    """
    Check for upcoming tasks and send push notifications
    Runs every minute from background scheduler
    """
    # 🌍 Fix: Use timezone-aware UTC now to match DB
    now = datetime.now(timezone.utc)
    
    # 1-3. Check for 20-minute, 10-minute, and Due Now reminders for Local & Google
    for mins in [20, 10, 0]:
        await process_reminders(db, now, minutes=mins)
        await process_google_reminders(db, now, minutes=mins)

    # 4. Check for completion feedback (tasks due in the past 5-10 mins, still pending)
    await check_task_completion_reminders(db, now)

    # 5. Check for Morning/Evening Summaries ☕🌙
    await check_and_send_summaries(db, now)

    # 🚀 ONE SINGLE COMMIT at the end of all checks to prevent greenlet conflicts
    await db.commit()

async def check_and_send_summaries(db: AsyncSession, now_utc: datetime):
    """
    Check if it's time to send Morning/Evening AI summaries
    """
    from app.services.ai_service import generate_ai_summary
    from app.models.user import User
    from sqlalchemy import select
    from datetime import time as dt_time # Use python standard time
    
    # Simple IST conversion for time check (since settings are in Local Time usually)
    now_ist = now_utc + timedelta(hours=5, minutes=30)
    current_time_str = now_ist.strftime("%H:%M")
    current_date_str = now_ist.strftime("%Y-%m-%d")

    # Fetch all users with settings
    query = select(User, UserSetting).join(UserSetting, User.id == UserSetting.user_id).filter(
        and_(
            UserSetting.push_enabled == True,
            UserSetting.fcm_token != None
        )
    )
    result = await db.execute(query)
    users_with_settings = result.all()

    for user, setting in users_with_settings:
        # --- MORNING CHECK ---
        if setting.morning_enabled and setting.morning_time == current_time_str:
            if setting.last_morning_summary_at != current_date_str:
                tasks = await get_user_tasks_for_day(db, user.id, now_ist.date())
                message = await generate_ai_summary("MORNING", user.full_name, tasks)
                if message:
                    await fcm_manager.send_notification(
                        token=setting.fcm_token,
                        title="Good Morning! ☀️",
                        body=message,
                        data={"type": "morning_summary"}
                    )
                    await record_notification(db, user.id, "Good Morning! ☀️", message, {"type": "morning_summary"})
                    setting.last_morning_summary_at = current_date_str
                    db.add(setting)

        # --- EVENING CHECK ---
        if setting.evening_enabled and setting.evening_time == current_time_str:
            if setting.last_evening_summary_at != current_date_str:
                tasks = await get_user_tasks_for_day(db, user.id, now_ist.date())
                message = await generate_ai_summary("EVENING", user.full_name, tasks)
                if message:
                    await fcm_manager.send_notification(
                        token=setting.fcm_token,
                        title="Evening Update 🌙",
                        body=message,
                        data={"type": "evening_summary"}
                    )
                    await record_notification(db, user.id, "Evening Update 🌙", message, {"type": "evening_summary"})
                    setting.last_evening_summary_at = current_date_str
                    db.add(setting)

async def get_user_tasks_for_day(db: AsyncSession, user_id: int, target_date):
    """Helper to fetch tasks for a specific user on a specific day using robust IST filtering"""
    from datetime import time, timedelta, timezone
    
    # Define IST bounds in UTC-like relative terms
    dt_ist_start = datetime.combine(target_date, time.min)
    dt_ist_end = datetime.combine(target_date, time.max)
    
    # Convert IST target range to approximate UTC range (wide net)
    # subtracting 5:30 to get UTC equivalent
    dt_utc_start = (dt_ist_start - timedelta(hours=5, minutes=30)).replace(tzinfo=timezone.utc)
    dt_utc_end = (dt_ist_end - timedelta(hours=5, minutes=30)).replace(tzinfo=timezone.utc)
    
    # Fetch tasks with a wider buffer (±1 Day)
    buffer = timedelta(days=1)
    query_start = dt_utc_start - buffer
    query_end = dt_utc_end + buffer
    
    query = select(Task).filter(
        and_(
            Task.user_id == user_id,
            Task.due_date >= query_start,
            Task.due_date <= query_end
        )
    ).order_by(Task.due_date)
    
    res = await db.execute(query)
    all_potential_tasks = res.scalars().all()
    
    # Filter strictly in Python
    tz_ist = timezone(timedelta(hours=5, minutes=30))
    tasks = []
    
    for t in all_potential_tasks:
        if not t.due_date: continue
        
        t_due = t.due_date
        if t_due.tzinfo is None:
            t_due = t_due.replace(tzinfo=timezone.utc)
            
        t_ist = t_due.astimezone(tz_ist)
        if t_ist.date() == target_date:
            tasks.append(t)
            
    return tasks

async def check_task_completion_reminders(db: AsyncSession, now: datetime):
    """
    Every 30 minutes after due time, check if user completed the task.
    Continues until status is 'completed'.
    """
    try:
        # 1. Find all pending tasks that are past due
        query = select(Task, UserSetting.fcm_token).join(
            UserSetting, Task.user_id == UserSetting.user_id
        ).filter(
            and_(
                Task.status == "pending",
                Task.due_date <= now, # Find all overdue tasks
                UserSetting.push_enabled == True,
                UserSetting.fcm_token != None
            )
        )

        result = await db.execute(query)
        overdue_tasks = result.all()
        
        if overdue_tasks:
            print(f"🧐 [Nudge] Checking {len(overdue_tasks)} potential overdue tasks...")

        for task, token in overdue_tasks:
            # Improved Logic:
            # 1. If we already poked them, wait 30 mins from THAT poke
            # 2. If never poked, wait 30 mins from Due Date
            last_ref = task.last_nudged_at
            if last_ref and last_ref.tzinfo is None:
                 last_ref = last_ref.replace(tzinfo=timezone.utc)

            due_ref = task.due_date
            if due_ref and due_ref.tzinfo is None:
                 due_ref = due_ref.replace(tzinfo=timezone.utc)

            # Determine baseline
            baseline_time = last_ref if last_ref else due_ref
            
            # Calculate gap
            delta_minutes = (now - baseline_time).total_seconds() / 60
            
            # Trigger if gap >= 30m
            if delta_minutes >= 30:
                print(f"🔄 [Nudge] Sending 30m follow-up for: '{task.title}' (Gap: {int(delta_minutes)}m)")
                # Use send_friendly_push with a special flag for nudges
                # We use -1 to indicate "Nudge/Poll"
                success = await send_friendly_push(db, task, token, lead_mins=-1)
                
                if success:
                    task.last_nudged_at = now
                    db.add(task)
    except Exception as e:
        print(f"❌ [Nudge] Error in nudge logic: {e}")

async def send_completion_poll(db: AsyncSession, task: Task, token: str):
    """Send a 'How did it go?' notification with interactive actions"""
    title = "Finished your task? ✅"
    body = f"Did you complete '{task.title}'? Tap to update."
    
    data = {
        "task_id": str(task.id),
        "type": "completion_poll",
        "title": task.title
    }

    # Using 'TASK_COMPLETION' category which the frontend will handle
    try:
        response = await fcm_manager.send_notification(
            token=token,
            title=title,
            body=body,
            data=data,
            click_action="TASK_COMPLETION"
        )
        if response is not None:
            await record_notification(db, task.user_id, title, body, data)
        return response is not None
    except ValueError as e:
        if str(e) == "STALE_TOKEN":
            await clear_stale_token(db, task.user_id)
        return False
    except Exception:
        return False

async def clear_stale_token(db: AsyncSession, user_id: int):
    """Clear a token that Firebase says is invalid"""
    try:
        query = select(UserSetting).filter(UserSetting.user_id == user_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()
        if settings:
            print(f"🧹 [Cleanup] Clearing stale FCM token for user {user_id}")
            settings.fcm_token = None
            db.add(settings)
    except Exception as e:
        print(f"❌ [Cleanup] Failed to clear token: {e}")

async def process_reminders(db: AsyncSession, now: datetime, minutes: int):
    """Process reminders for a specific lead time (10m or 20m)"""
    
    # Define range to catch tasks even if scheduler is slightly delayed
    start_range = now + timedelta(minutes=minutes - 1)
    end_range = now + timedelta(minutes=minutes + 1)
    
    if minutes == 20:
        notified_col = Task.notified_20m
    elif minutes == 10:
        notified_col = Task.notified_10m
    else:
        notified_col = Task.notified_due
    
    
    # Find pending tasks within the time window that haven't been notified for this lead time
    query = select(Task, UserSetting.fcm_token).join(
        UserSetting, Task.user_id == UserSetting.user_id
    ).filter(
        and_(
            Task.status == "pending",
            Task.due_date >= start_range,
            Task.due_date <= end_range,
            notified_col == False,
            UserSetting.push_enabled == True,
            UserSetting.fcm_token != None
        )
    )
    
    result = await db.execute(query)
    reminders = result.all()
    
    for task, token in reminders:
        # 🤖 Generate AI message
        due_time_str = format_local_time(task.due_date)
        ai_message = await generate_friendly_reminder(task.title, due_time_str, minutes)
        
        success = await send_friendly_push(db, task, token, minutes, ai_message)
        if success:
            if minutes == 20: task.notified_20m = True
            elif minutes == 10: task.notified_10m = True
            else: task.notified_due = True
            
            db.add(task)
            print(f"🚀 [AI-FCM] Sent {minutes}m reminder for: {task.title}")

async def process_google_reminders(db: AsyncSession, now: datetime, minutes: int):
    """Fetch and process reminders for Google Calendar/Tasks"""
    # Find users who are synced
    from sqlalchemy import select
    query = select(User, UserSetting).join(UserSetting, User.id == UserSetting.user_id).filter(
        and_(
            User.google_refresh_token != None,
            UserSetting.push_enabled == True,
            UserSetting.fcm_token != None
        )
    )
    res = await db.execute(query)
    users = res.all()
    
    for user, setting in users:
        try:
            # Check a wider window for Google to be safe
            window_start = now + timedelta(minutes=minutes - 1)
            window_end = now + timedelta(minutes=minutes + 1)
            
            data = await google_calendar_service.get_google_data(
                user, db, 
                time_min=window_start.isoformat().replace('+00:00', 'Z'),
                time_max=window_end.isoformat().replace('+00:00', 'Z')
            )
            
            # Combine all Google items
            all_items = []
            for e in data.get("events", []):
                start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
                if start: all_items.append({"id": e.get("id"), "title": e.get("summary", "Event"), "time": start, "type": "meeting"})
            
            for t in data.get("tasks", []):
                due = t.get("due")
                if due: all_items.append({"id": t.get("id"), "title": t.get("title", "Task"), "time": due, "type": "task"})

            from dateutil import parser
            for item in all_items:
                try:
                    item_time = parser.parse(item["time"])
                    if item_time.tzinfo is None: item_time = item_time.replace(tzinfo=timezone.utc)
                    
                    # Check if it falls exactly in our window
                    if window_start <= item_time <= window_end:
                        # Check if already notified for this stage to avoid spam
                        notif_key = f"google_{item['id']}_{minutes}"
                        check_query = select(Notification).where(
                            and_(
                                Notification.user_id == user.id,
                                Notification.data['google_notif_key'].astext == notif_key
                            )
                        )
                        existing = await db.execute(check_query)
                        if existing.scalar_one_or_none():
                            continue

                        # 🤖 Generate AI message
                        due_time_str = format_local_time(item_time)
                        ai_message = await generate_friendly_reminder(item["title"], due_time_str, minutes)

                        # Send Push
                        success = await fcm_manager.send_notification(
                            token=setting.fcm_token,
                            title=f"LARA: {ai_message[:30]}...",
                            body=ai_message,
                            data={"type": "google_reminder", "google_id": item["id"], "lead": str(minutes)}
                        )
                        
                        if success:
                            # Record so we don't repeat
                            await record_notification(
                                db, user.id, "Google Reminder", ai_message, 
                                {"type": "google_reminder", "google_notif_key": notif_key}
                            )
                            print(f"🚀 [AI-Google] Sent {minutes}m reminder for: {item['title']}")
                except Exception as e:
                    logger.error(f"Error processing Google item: {e}")
        except Exception as e:
            logger.error(f"Failed to process Google reminders for user {user.id}: {e}")
    
    # ❌ Local commit removed to prevent greenlet conflicts

def format_local_time(dt: datetime):
    """Helper to convert UTC from DB to Local Time (IST +5:30) for display"""
    if not dt:
        return "soon"
    
    # Check if dt is aware, if not assume it's UTC (as it comes from DB)
    if dt.tzinfo is None:
        # DB usually stores UTC
        local_dt = dt + timedelta(hours=5, minutes=30)
    else:
        # If it has tz info, convert it (simple version for now)
        # Note: In a real prod app, we'd use user's saved timezone
        local_dt = dt + timedelta(hours=5, minutes=30)
        
    return local_dt.strftime('%I:%M %p') # Changed to 12-hour format with AM/PM for friendliness

async def get_natural_message(task: Task, lead_mins: int):
    """Generate the friendly, natural messages requested by user"""
    title = task.title.lower()
    due_time = format_local_time(task.due_date)
    
    # 1. Custom messages for specific keywords at Due Time (0 mins) OR Nudges (-1)
    if lead_mins == 0 or lead_mins == -1:
        # User requested NO "Still pending" prefix for any state
        # We keep the friendly tone without the nag prefix
        
        if "call" in title:
            # e.g., "call mom" -> "Hey! Don't forget to call mom 😊"
            return f"Hey! Don't forget to {task.title} 😊", f"Just a friendly reminder for {due_time}."
        if "milk" in title:
            return f"Quick reminder to buy milk 🥛", f"Hope you don't forget!"
        if "groceries" in title or "buy" in title:
            return f"Quick reminder to {task.title} ❤️", "You got this!"
        if "meeting" in title or "scrum" in title:
            return f"Meeting time: {task.title} ⏰", f"Starting at {due_time}."
        
        # Default Due Time / Nudge
        if lead_mins == -1:
             # Even for nudges, keep it simple
             return f"Follow up: {task.title} ⏳", "Did you complete this task yet? Tap to update."
        
        # Friendly Default Messages for Due Time
        titles = [
            f"Hey! Don't forget: {task.title} 😊",
            f"Friendly nudge: {task.title} ✨",
            f"It's time for: {task.title} 🚀",
            f"Reminder: {task.title} ❤️"
        ]
        chosen_title = random.choice(titles)
        return chosen_title, f"Scheduled for {due_time}."

    # 2. Pre-reminders (10m, 20m)
    starters = ["Friendly reminder:", "Heads up!", "Quick note:", "Lara here:"]
    starter = random.choice(starters)
    
    if lead_mins == 10:
        return f"10m Countdown: {task.title} ⏳", f"{starter} {task.title} at {due_time}."
    
    return f"{task.title} soon! 🔔", f"{starter} {task.title} scheduled for {due_time}."

async def send_friendly_push(db: AsyncSession, task: Task, token: str, lead_mins: int, ai_message: str = None):
    """Send a human-friendly FCM notification with natural language"""
    
    if ai_message:
        title_text = "LARA Update ✨" # Simple title, AI handles body
        body_text = ai_message
    else:
        # Fallback to old logic if AI fails
        title_text, body_text = await get_natural_message(task, lead_mins)

    # Specific override for medicine
    if task.type == "medicine" and lead_mins == 0:
        title_text = "Medicine Time! 💊"
        body_text = f"Don't forget to take {task.title} at {format_local_time(task.due_date)}."

    is_nudge = lead_mins == -1
    is_due = lead_mins == 0
    
    data = {
        "task_id": str(task.id),
        "type": "completion_poll" if (is_nudge or is_due) else "reminder",
        "lead_time": str(lead_mins)
    }
    
    try:
        # ✅ Buttons appear for 'Due Now' (0m) AND 'Nudges' (-1)
        # For pre-notifications (10, 20), click_act will be None
        click_act = "TASK_COMPLETION" if (is_due or is_nudge) else None
        
        response = await fcm_manager.send_notification(
            token=token,
            title=title_text,
            body=body_text,
            data=data,
            click_action=click_act
        )
        if response is not None:
            await record_notification(db, task.user_id, title_text, body_text, data)
        return response is not None
    except ValueError as e:
        if str(e) == "STALE_TOKEN":
            await clear_stale_token(db, task.user_id)
        return False
    except Exception as e:
        logger.error(f"Error sending push: {e}")
        return False

async def record_notification(db: AsyncSession, user_id: int, title: str, body: str, data: dict = None):
    """Save a copy of the notification to the database for the inbox"""
    try:
        # ✅ Filter: Only save "Due Now" (0m).
        # Skip 10m/20m countdowns AND Skip Nudges (completion_poll) to keep inbox clean.
        # User request: "show only confirmed notification" -> interpret as only the main reminders?
        # Or maybe only when they confirm? No, likely they want only the main "It's Time" alerts.
        
        should_skip = False
        if data:
            # Skip countdowns unless it's a Google reminder we need to track
            if data.get("type") != "google_reminder":
                if data.get("lead_time") in ["10", "20"]:
                    should_skip = True
            
            # Skip completion polls (follow-ups)
            if data.get("type") == "completion_poll":
                should_skip = True
        
        if should_skip:
            return

        new_notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            data=data # Store as dict directly for JSONB
        )
        db.add(new_notif)
        # ❌ REMOVED db.commit() from here to prevent session expiration in loops
        # Commit will be handled by the calling batch process
    except Exception as e:
        logger.error(f"❌ [Inbox] Failed to record notification: {e}")
