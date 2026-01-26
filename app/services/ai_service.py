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
        # 🛡️ Enhanced Regex: Supports HH:MM, HH o'clock, HH AM/PM, and "at HH"
        regex_match = re.search(r'\b(?P<hour>\d{1,2})(?::(?P<min>\d{2}))?\s*(?P<suffix>o\'?\s*clock|oclock|am|pm)?\b', user_text, re.IGNORECASE)
        if regex_match and not (regex_match.group("suffix") or re.search(r'\b(?:at|by|around|for)\b', user_text[:regex_match.start()], re.IGNORECASE)):
            regex_match = None # Lone number without context, ignore

        extracted_date = None
        match_text = ""

        if regex_match:
            try:
                h = int(regex_match.group("hour"))
                m = int(regex_match.group("min") or 0)
                suffix = (regex_match.groupdict().get("suffix") or "").lower()
                
                candidates = []
                if 'am' in suffix: candidates = [h if h != 12 else 0]
                elif 'pm' in suffix: candidates = [h + 12 if h != 12 else 12]
                else: candidates = sorted(list(set([h if h != 12 else 0, h + 12 if h != 12 else 12])))

                dt_candidates = []
                for h_val in candidates:
                    if 0 <= h_val < 24:
                        dt_candidates.append(now_ist.replace(hour=h_val, minute=m, second=0, microsecond=0))
                
                dt_candidates.sort()
                future = [d for d in dt_candidates if d > (now_ist + dt_module.timedelta(minutes=1))]
                extracted_date = future[0] if future else (dt_candidates[0] + dt_module.timedelta(days=1))
                match_text = regex_match.group(0)
                logger.info(f"🎯 [Regex] Matched '{match_text}' -> {extracted_date}")
            except Exception as e:
                logger.error(f"Regex error: {e}")

        # 🧪 NLP Fallback
        if not extracted_date:
            matches = search_dates(user_text, settings={'RELATIVE_BASE': now_ist, 'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Kolkata', 'TO_TIMEZONE': 'Asia/Kolkata'})
            if matches:
                temp_match, temp_dt = matches[-1]
                # 🛡️ SECURITY: Only trust NLP if it matched a word like 'today', 'tomorrow', 'at', 'pm', or a full time pattern.
                # This stops random numbers like "28" or "10" (from "Task 28") being seen as dates/times.
                trigger_keywords = ["today", "tomorrow", "tonight", "at", "by", "for", "on", "am", "pm", "clock", "morning", "evening", "afternoon", "night"]
                is_valid_time_mention = any(w in temp_match.lower() for w in trigger_keywords) or ":" in temp_match
                
                if is_valid_time_mention:
                    match_text = temp_match
                    extracted_date = temp_dt if temp_dt.tzinfo else temp_dt.replace(tzinfo=tz_ist)
                    
                    # 🌅 Handle generic today/tomorrow (00:00)
                    if extracted_date.hour == 0 and extracted_date.minute == 0 and not re.search(r'\d', match_text):
                        if extracted_date.date() == now_ist.date():
                             extracted_date = now_ist + dt_module.timedelta(hours=2) # Default Rule
                        else:
                             extracted_date = extracted_date.replace(hour=10, minute=0) # 10 AM tomorrow
                    
                    # Past Fix
                    if (extracted_date - now_ist).total_seconds() < -60:
                        extracted_date += dt_module.timedelta(days=1)
                else:
                    logger.info(f"⏭️  [NLP] Ignoring suspicious match (no keywords): '{temp_match}'")

        # 🚀 DEFAULT RULE: If no valid time found, use Today + 2 Hours
        if not extracted_date:
            extracted_date = now_ist + dt_module.timedelta(hours=2)
            logger.info(f"⏰ [Default] No time mentioned, applied Today + 2h: {extracted_date}")

        # Smart Vague Clarification (only if no digits used)
        if not re.search(r'\d', match_text) and any(w in input_text for w in ["morning", "evening", "afternoon"]):
            suggested = 10 if "morning" in input_text else (15 if "afternoon" in input_text else 18)
            extracted_date = extracted_date.replace(hour=suggested, minute=0, second=0, microsecond=0)
            if extracted_date < now_ist and (extracted_date.date() == now_ist.date()): 
                extracted_date += dt_module.timedelta(days=1)

        # --- C. Finalize and Save (Immediate) ---
        clean_title = user_text
        if match_text:
             clean_title = re.sub(re.escape(match_text), "", clean_title, flags=re.IGNORECASE).strip()

        # 🧹 Broad residue cleaning
        clean_title = re.sub(r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm|o\'?clock)\b', '', clean_title, flags=re.IGNORECASE).strip()
        clean_title = re.sub(r'\b(at|on|for|in|to|with|by|around)\s*$', '', clean_title, flags=re.IGNORECASE).strip()

        # 👥 Pronoun Shift
        repls = [(r"\bI'm\b", "You're"), (r"\bi am\b", "you are"), (r"\bI\b", "You"), (r"\bmy\b", "your"), (r"\bme\b", "you"), (r"\bam\b", "are")]
        for p, r in repls: clean_title = re.sub(p, r, clean_title, flags=re.IGNORECASE).strip()

        # 🧹 Leading Filler Clean
        for v in ["remind me to", "remind me", "add task to", "i need to", "create task", "call"]:
            clean_title = re.sub(r'^' + v + r'\s*', '', clean_title, flags=re.IGNORECASE).strip()

        final_title = (clean_title or "New Task").capitalize()
        pretty_time = extracted_date.strftime("%I:%M %p")
        day_label = "today" if extracted_date.date() == now_ist.date() else ("tomorrow" if (extracted_date.date() - now_ist.date()).days == 1 else extracted_date.strftime("%b %d"))

        logger.info(f"💾 Saving: '{final_title}' for {extracted_date}")
        return {
            "title": final_title, "time": extracted_date.isoformat(), 
            "type": "reminder" if "remind" in input_text else "task",
            "response_text": f"Got it! Scheduled '{final_title}' for {day_label} at {pretty_time} IST. ✅",
            "is_complete": True 
        }

    except Exception as exc:
        logger.error(f"LARA Error: {exc}")
        return {"title": "", "time": None, "type": "task", "is_complete": False, "response_text": "I'm sorry, could you repeat that? 🙏"}

    except Exception as exc:
        logger.error(f"LARA Critical Error: {exc}")
        return {
            "title": "", "time": None, "type": "task", "is_complete": False,
            "response_text": "I'm sorry, I had some trouble. Could you repeat that? 🙏"
        }

    except Exception as exc:
        logger.error(f"LARA Critical Error: {exc}")
        return {
            "title": "", "time": None, "type": "task", "is_complete": False,
            "response_text": "I'm sorry, I had some trouble. Could you repeat that? 🙏"
        }
