import logging
import re
# Core services for AI processing
from datetime import datetime, timedelta, timezone
import random
import dateparser
from dateparser.search import search_dates

logger = logging.getLogger(__name__)

async def generate_ai_summary(summary_type: str, user_name: str, tasks: list):
    """
    Generate a formatted summary using templates.
    """
    try:
        if not tasks:
            if summary_type == "MORNING":
                return f"Good morning {user_name}! ☀️ You have no tasks scheduled for today. Enjoy your free time!"
            else:
                return f"Evening {user_name}! 🌙 You're all caught up. No pending tasks for today. Great job!"

        task_count = len(tasks)
        task_list_str = ""
        
        # Simple task formatting
        for i, t in enumerate(tasks[:3]): # Show max 3 tasks details
            time_part = t.due_date.strftime("%I:%M %p") if t.due_date else "Anytime"
            task_list_str += f"\n• {t.title} ({time_part})"
        
        if task_count > 3:
            task_list_str += f"\n...and {task_count - 3} more."

        if summary_type == "MORNING":
            greetings = [
                f"Rise and shine {user_name}! ☀️",
                f"Good Morning {user_name}! ☕",
                f"Ready for the day {user_name}? 🚀"
            ]
            intro = random.choice(greetings)
            return f"{intro} You have {task_count} tasks today:{task_list_str}\n\nLet's get started!"
            
        else: # EVENING
            # Logic: Calculate stats
            completed = sum(1 for t in tasks if t.status == 'completed')
            pending = sum(1 for t in tasks if t.status == 'pending')
            
            return f"Evening Update 🌙\nYou completed {completed} tasks today. {pending} left pending.\nCheck the app to plan for tomorrow!"

    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return None

async def process_voice_command(user_text: str, current_time: str = None):
    """
    LARA Conversational Voice Parser.
    Follows a multi-step confirmation workflow.
    """
    import datetime as dt_module
    
    tz_ist = dt_module.timezone(dt_module.timedelta(hours=5, minutes=30))
    now_ist = dt_module.datetime.now(dt_module.timezone.utc).astimezone(tz_ist)
    
    input_text = user_text.lower().strip()
    
    # --- STEP 1: Handle Confirmation/Cancellation ---
    # We use 'current_time' parameter as a signal if the frontend is already in a 'pending' state
    # But a cleaner way is to check the text for confirmation keywords.
    confirm_words = ['yes', 'confirm', 'save', 'okay', 'ok', 'do it', 'yep', 'sure']
    cancel_words = ['no', 'cancel', 'stop', 'dont', "don't", 'nevermind']
    
    # Check if this input is a response to a PREVIOUS confirmation request
    # Logic: if the input is JUST a confirmation word
    if input_text in confirm_words:
        return {
            "title": "", # Frontend will use its cached pending title
            "time": None,
            "type": "task",
            "response_text": "Done! Your reminder is saved. ✨",
            "is_complete": True # 🚀 THIS TRIPS THE SAVE IN FRONTEND
        }
    
    if input_text in cancel_words:
        return {
            "title": "",
            "time": None,
            "type": "task",
            "response_text": "Alright, I won’t add it. 😊",
            "is_complete": False,
            "is_cancelled": True # Signal to frontend to clear state
        }

    try:
        # --- STEP 2: Logic for New Task or Missing Detail ---
        # Extract matches
        matches = search_dates(user_text, settings={
            'RELATIVE_BASE': now_ist, 
            'PREFER_DATES_FROM': 'future', 
            'TIMEZONE': 'Asia/Kolkata', 
            'TO_TIMEZONE': 'Asia/Kolkata'
        })
        
        extracted_date = None
        match_text = ""
        
        # Manual Regex for "at 4" or "at 10" or "o'clock"
        regex_match = re.search(r'\b(\d{1,2})\s*(?:o\'?\s*clock|oclock|am|pm)\b', user_text, re.IGNORECASE)
        if not regex_match:
             regex_match = re.search(r'\bat\s+(\d{1,2})\b', user_text, re.IGNORECASE)

        if regex_match:
            try:
                h = int(regex_match.group(1))
                candidates = []
                # Simple AM/PM logic for IST
                v_am = h if h != 12 else 0
                v_pm = h + 12 if h != 12 else 12
                if v_pm >= 24: v_pm -= 12
                for h_val in sorted(list(set([v_am, v_pm]))):
                    candidates.append(now_ist.replace(hour=h_val, minute=0, second=0, microsecond=0))
                candidates.sort()
                future = [d for d in candidates if d > (now_ist + dt_module.timedelta(minutes=1))]
                extracted_date = future[0] if future else (candidates[0] + dt_module.timedelta(days=1))
                match_text = regex_match.group(0)
            except: pass

        if not extracted_date and matches:
            match_text, match_dt = matches[-1]
            extracted_date = match_dt if match_dt.tzinfo else match_dt.replace(tzinfo=tz_ist)
            # Past Fix
            if (extracted_date - now_ist).total_seconds() < -60: # 1 min buffer
                 extracted_date += dt_module.timedelta(days=1)

        # --- STEP 3: Persona-Driven Branching ---
        
        # A. If NO TIME found at all
        if not extracted_date:
            return {
                "title": user_text.capitalize(),
                "time": None,
                "type": "task",
                "response_text": "Sure. At what time should I set this reminder in IST? 🕒",
                "is_complete": False
            }

        # B. If time is VAGUE (e.g. "morning", "evening", "tomorrow" without hour)
        # Check if dateparser gave us a default 00:00 or if user just said "today"
        is_vague = False
        if extracted_date.hour == 0 and extracted_date.minute == 0:
            if "midnight" not in input_text: is_vague = True
        elif "evening" in input_text and not re.search(r'\d', match_text):
            is_vague = True

        if is_vague:
            suggested_hour = 10 if "morning" in input_text else 18 # 10am or 6pm
            day_str = "today" if extracted_date.date() == now_ist.date() else "tomorrow"
            
            # 🕒 Update the date object to match the suggestion
            extracted_date = extracted_date.replace(hour=suggested_hour, minute=0, second=0, microsecond=0)
            
            return {
                "title": user_text.replace(match_text, "").strip().capitalize(),
                "time": extracted_date.isoformat(), # Updated to 10am or 6pm
                "type": "task",
                "response_text": f"Do you mean {day_str} at {suggested_hour % 12 or 12} {'PM' if suggested_hour >= 12 else 'AM'} IST? 🧐",
                "is_complete": False
            }

        # C. Ready for Final Confirmation (Rule 6)
        clean_title = user_text.replace(match_text, "").strip()
        # Clean title logic (verbs, pronouns)
        action_verbs = ["remind me to", "add task to", "i need to", "call", "buy", "meet"]
        for v in action_verbs: clean_title = re.sub(r'^' + v, '', clean_title, flags=re.IGNORECASE).strip()
        
        # Personalize Pronouns
        repls = [(r"\bI\b", "You"), (r"\bmy\b", "your"), (r"\bme\b", "you")]
        for p, r in repls: clean_title = re.sub(p, r, clean_title, flags=re.IGNORECASE).strip()
        
        final_title = (clean_title or "New Task").capitalize()
        pretty_time = extracted_date.strftime("%I:%M %p")
        day_label = "Today" if extracted_date.date() == now_ist.date() else "Tomorrow"
        
        return {
            "title": final_title,
            "time": extracted_date.isoformat(),
            "type": "reminder" if "remind" in input_text else "task",
            "response_text": f"Okay, I will add this reminder:\nTask: {final_title}\nTime: {day_label} at {pretty_time} IST\nShould I confirm and save it? 😊",
            "is_complete": False # 🛑 ALWAYS False here, waiting for "Yes"
        }

    except Exception as exc:
        logger.error(f"LARA Critical Error: {exc}")
        return {
            "title": "", "time": None, "type": "task", "is_complete": False,
            "response_text": "I'm sorry, I'm having a bit of trouble. Mind saying that again? 🙏"
        }
