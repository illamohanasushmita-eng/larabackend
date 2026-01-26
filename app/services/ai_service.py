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
    Advanced voice parser using dateparser for natural language time extraction.
    Ensures safe scoping and logic for IST/UTC handling.
    """
    import datetime as dt_module
    
    # Standard IST Definition
    tz_ist = dt_module.timezone(dt_module.timedelta(hours=5, minutes=30))

    try:
        # Determine Base Time in UTC
        if current_time:
            try:
                base_time_utc = dt_module.datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            except ValueError:
                base_time_utc = dt_module.datetime.now(dt_module.timezone.utc)
        else:
            base_time_utc = dt_module.datetime.now(dt_module.timezone.utc)

        # Convert Base Time to IST for logic
        base_time_ist = base_time_utc.astimezone(tz_ist)
        
        logger.info(f"Processing Voice: '{user_text}' (IST Ref: {base_time_ist})")

        response = {
            "title": "",
            "time": None,
            "type": "task",
            "is_complete": False,
            "response_text": ""
        }

        matches = None
        extracted_date = None
        match_text = ""
        clean_text = user_text

        # 1. 🛡️ Prioritize Manual Regex for "o'clock" and "at X"
        # Expanded to handle: "o clock", "o'clock", "oclock", "am/pm"
        fallback_match = re.search(r'\b(\d{1,2})\s*(?:o\'?\s*clock|oclock|am|pm)\b', user_text, re.IGNORECASE)
        if not fallback_match:
             # Handle "at 4" or "at 10" patterns
             fallback_match = re.search(r'\bat\s+(\d{1,2})\b', user_text, re.IGNORECASE)
        
        if fallback_match:
            try:
                h = int(fallback_match.group(1))
                candidates = []
                # Handle 12 AM/PM correctly (12 AM -> 00, 12 PM -> 12)
                v_am = h if h != 12 else 0
                v_pm = h + 12 if h != 12 else 12
                # If user says 13-23, they likely mean 24h format, which fits v_pm
                if v_pm >= 24: v_pm -= 12
                
                # Check Today's candidates
                for h_val in sorted(list(set([v_am, v_pm]))):
                    candidates.append(base_time_ist.replace(hour=h_val, minute=0, second=0, microsecond=0))
                
                candidates.sort()
                future_candidates = [d for d in candidates if d > (base_time_ist + dt_module.timedelta(minutes=1))]
                
                if future_candidates:
                    extracted_date = future_candidates[0]
                    logger.info(f"🎯 [Regex] Found future candidate for today: {extracted_date}")
                else:
                    # Both passed today, assume morning of next day 
                    # Use v_am (or at least h) for tomorrow
                    extracted_date = candidates[0] + dt_module.timedelta(days=1)
                    logger.info(f"🎯 [Regex] Time passed today, moving to tomorrow: {extracted_date}")
                
                match_text = fallback_match.group(0)
            except Exception as e:
                logger.error(f"Regex parsing exception: {e}")

        # 2. 🧪 Use dateparser if regex didn't catch it
        if not extracted_date:
            try:
                matches = search_dates(user_text, settings={
                    'RELATIVE_BASE': base_time_ist, 
                    'PREFER_DATES_FROM': 'future', 
                    'TIMEZONE': 'Asia/Kolkata', 
                    'TO_TIMEZONE': 'Asia/Kolkata', 
                    'PREFER_DAY_OF_MONTH': 'current'
                })
                if matches:
                    match_text, match_dt = matches[-1]
                    extracted_date = match_dt
                    
                    if extracted_date.tzinfo is None:
                        extracted_date = extracted_date.replace(tzinfo=tz_ist)
                    else:
                        extracted_date = extracted_date.astimezone(tz_ist)

                    # AM/PM Ambiguity Check for Dateparser
                    is_ambiguous = "am" not in match_text.lower() and "morning" not in match_text.lower()
                    if is_ambiguous and extracted_date < base_time_ist and extracted_date.date() == base_time_ist.date():
                        potential_pm = extracted_date + dt_module.timedelta(hours=12)
                        if potential_pm > base_time_ist and potential_pm.date() == base_time_ist.date():
                             extracted_date = potential_pm
                             logger.info(f"🧠 [NLP] Flipped AM to PM: {extracted_date}")

                    # 🌅 [Smart Midnight Fix]
                    # Only default to 9 AM if the match is purely a day (like "tomorrow") 
                    # AND it has no numbers, no am/pm, etc.
                    if extracted_date.hour == 0 and extracted_date.minute == 0:
                        has_time_cue = re.search(r'\d', match_text) or "am" in match_text.lower() or "pm" in match_text.lower() or ":" in match_text
                        if not has_time_cue and "midnight" not in user_text.lower():
                            extracted_date = extracted_date.replace(hour=9, minute=0)
                            logger.info(f"🌅 [NLP] Defaulted vague date '{match_text}' to 9:00 AM")

                    # Past Fix (Next Day) - Only for NLP
                    if (extracted_date - base_time_ist).total_seconds() < -300:
                        if "yesterday" not in match_text.lower():
                            extracted_date += dt_module.timedelta(days=1)
                            logger.info(f"🧠 [NLP] Past time detected, bumped to tomorrow: {extracted_date}")
                
            except Exception as dp_err:
                logger.error(f"Dateparser error: {dp_err}")

        # 3. Final Fallback (3 hours from now)
        if not extracted_date:
            extracted_date = base_time_ist + dt_module.timedelta(hours=3)
            logger.info(f"🆘 [Fallback] No date found, using +3h: {extracted_date}")
            clean_text = user_text
        else:
            clean_text = user_text.replace(match_text, "").strip()

        # Save ISO format (IST)
        response["time"] = extracted_date.isoformat()

        # Cleanup leftover prepositions
        clean_text = re.sub(r'\b(at|on|for)\s*$', '', clean_text, flags=re.IGNORECASE).strip()

        # Title Selection
        action_verbs = ["call", "email", "text", "buy", "get", "meet", "schedule", "pay", "send", "clean", "do", "study", "go to"]
        lower_text = user_text.lower()
        
        if any(w in lower_text for w in ["meeting", "meet", "appointment"]): response["type"] = "meeting"
        elif any(w in lower_text for w in ["remind", "reminder", "alarm"]): response["type"] = "reminder"
        
        final_start = 0
        remind_m = re.search(r"remind\s+(?:me|us)\s+to\s+", clean_text.lower())
        if remind_m:
            final_start = remind_m.end()
        else:
            verb_m = re.search(r"\b(" + "|".join(action_verbs) + r")\b", clean_text.lower())
            if verb_m: final_start = verb_m.start()

        real_title = clean_text[final_start:].strip()
        real_title = re.sub(r"\s+(please|thanks|thank you)\W*$", "", real_title, flags=re.IGNORECASE).strip()
        
        # Pronoun replacement
        repls = [(r"\bI'm\b", "You're"), (r"\bI\b", "You"), (r"\bmy\b", "your"), (r"\bme\b", "you"), (r"\bam\b", "are")]
        for p, r in repls:
            real_title = re.sub(p, r, real_title, flags=re.IGNORECASE)

        response["title"] = (real_title or "New Task").capitalize()
        response["is_complete"] = True
        
        # Pretty display time
        pretty_time = extracted_date.strftime("%I:%M %p")
        
        # Determine day label for voice response
        day_label = "today" if extracted_date.date() == base_time_ist.date() else "tomorrow"
        response["response_text"] = f"Got it! Scheduled '{response['title']}' for {day_label} at {pretty_time}. ✅"

        return response

    except Exception as exc:
        logger.error(f"Voice processing CRITICAL fail: {exc}")
        return {
            "title": "",
            "time": None,
            "type": "task",
            "response_text": "I had trouble understanding that. Could you try again?",
            "is_complete": False
        }
