import logging
import re
from datetime import datetime, timedelta
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
    Supports: "tomorrow at 10am", "in 30 mins", "next friday", "at 6pm"
    """
    try:
        # 1. Setup Base Time
        # Use provided current_time (ISO string) or system time
        if current_time:
            try:
                base_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            except ValueError:
                base_time = datetime.now()
        else:
            base_time = datetime.now()

        # Ensure timezone unaware for simpler comparisons/math if needed, or stick to offset-naive for calculation
        # But if fromisoformat returns offset-aware, we should be consistent.
        # Let's use valid local time logic.
        # Ideally, we work with naive objects if the app is simple single-timezone,
        # OR we just trust dateparser to handle relative deltas.
        
        # For 'today' checks, we need to know what 'today' is in the user's timezone.
        # Since we use 'base_time' as RELATIVE_BASE, dateparser handles it.
        
        logger.info(f"Processing Voice: '{user_text}' at {base_time}")

        response = {
            "title": "",
            "time": None,
            "type": "task",
            "is_complete": False,
            "response_text": ""
        }

        # 2. Extract Date/Time
        # settings: PREFER_DATES_FROM='future' helps resolve "10am" to tomorrow if 10am passed? 
        # Actually 'future' prefers future dates for ambiguous periods.
        extracted_date = None
        extracted_text = ""
        
        try:
            # search_dates returns list of (text, datetime)
            matches = search_dates(user_text, settings={'RELATIVE_BASE': base_time, 'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Kolkata', 'TO_TIMEZONE': 'Asia/Kolkata'})
        except Exception as dp_err:
            logger.error(f"Dateparser error: {dp_err}")
            matches = None

        if matches:
            # Usually the last match is the most relevant if multiple dates mentioned?
            # Or the one that looks like a due date.
            # Example: "Schedule meeting on Friday at 5pm" -> "Friday at 5pm" might be one match or two.
            # dateparser usually grabs the longest chunk if logical.
            
            # We take the match that covers the "time" intent
            # Let's pick the last one found as it's often at the end of sentence "Call mom at 5"
            match_text, match_dt = matches[-1]
            
            extracted_date = match_dt
            extracted_text = match_text
            
            # Custom Rule: "If time passes for today -> schedule for next day"
            # matches[-1] might be "10 am"
            # If base_time is 2pm, dateparser with 'future' might yield tomorrow 10am OR today 10am depending on config.
            # Let's explicitly enforce the rule:
            # If the user SAID "today 10am", we assume they mean it (even if past).
            # If the user SAID "10am" (implied today) and it's past, move to tomorrow.
            
            # Heuristic: Check if 'today' or explicit date was in the text.
            # If 'today' or 'tomorrow' or 'monday' NOT in match_text, and only time was matched...
            # This is hard to detect perfectly.
            # Simpler Rule: If the extracted date is more than 5 minutes in the PAST relative to base_time,
            # AND the user text did NOT explicitly say "yesterday" or a past date keyword,
            # THEN add 1 day.
            
            # Ensure timezone awareness (Asia/Kolkata) if needed, but for now we rely on consistent base_time
            # If base_time is naive, result is naive. If base_time is aware, result is aware.
            # The user requested explicit Asia/Kolkata handling.
            # We can force the timezone if the result is naive.
            
            import pytz
            tz = pytz.timezone('Asia/Kolkata')
            
            # Helper to localize if naive
            def ensure_tz(dt):
                if dt.tzinfo is None:
                    return tz.localize(dt)
                return dt.astimezone(tz)

            extracted_date = ensure_tz(extracted_date)
            base_time = ensure_tz(base_time)

            time_diff = extracted_date - base_time
            
            # If it's in the past (allow 5 min buffer)
            if time_diff.total_seconds() < -300: 
                # Check for explicit past keywords to avoid altering "Remind me what I did yesterday" (though that's not a task)
                lower_match = match_text.lower()
                if "yesterday" not in lower_match and "last" not in lower_match:
                     logger.info(f"Time {extracted_date} is in past. Moving to next day.")
                     extracted_date += timedelta(days=1)

            # Format time for response (ISO with timezone)
            response["time"] = extracted_date.isoformat()
            
            # Clean title: Remove the matched date string from the original text
            # We use replace, but be careful of overlapping/repeated words.
            # Use regex to replace the specific match index if possible, OR string replace.
            # match_text usually matches exactly from source.
            clean_text = user_text.replace(match_text, "").strip()
            
            # Cleanup extra prepositions left over: "Call mom at" -> "Call mom"
            clean_text = re.sub(r'\bat\s*$', '', clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r'\bon\s*$', '', clean_text, flags=re.IGNORECASE).strip()
            
        else:
            # 3. Default Time (+3 hours)
            clean_text = user_text
            default_due = base_time + timedelta(hours=3)
            # Start of next hour for cleanliness? Or exact +3h
            # Requirement: "current time + 3 hours"
            response["time"] = default_due.isoformat()
            extracted_date = default_due # For message formatting

        # 4. Smart Title Extraction (Verbs)
        # Similar to previous logic but on the clean_text
        
        action_verbs = [
            "call", "email", "text", "message", "whatsapp",
            "buy", "get", "purchase", "order",
            "meet", "schedule", "attend",
            "pay", "transfer", "send",
            "clean", "wash", "fix", "repair",
            "finish", "submit", "complete", "do",
            "read", "write", "study", "visit", "go to"
        ]
        
        lower_clean = clean_text.lower()
        final_start_index = 0
        
        # Priority: "Remind me to"
        remind_match = re.search(r"remind\s+(?:me|us)\s+to\s+", lower_clean)
        
        if remind_match:
            final_start_index = remind_match.end()
        else:
            # Verb Search
            verb_pattern = r"\b(" + "|".join(action_verbs) + r")\b"
            verb_match = re.search(verb_pattern, lower_clean)
            if verb_match:
                # If verb is 'start' of sentence (ignoring filler "I want to...")
                final_start_index = verb_match.start()
            else:
                # Fallback prefixes
                prefixes = [
                    r"add\s+a\s+task\s+to\s+", r"add\s+task\s+to\s+",
                    r"create\s+a\s+task\s+to\s+", r"new\s+task\s+",
                    r"i\s+need\s+to\s+", r"i\s+have\s+to\s+", r"please\s+"
                ]
                for p in prefixes:
                    m = re.match(p, lower_clean)
                    if m:
                        final_start_index = m.end()
                        break
        
        real_title = clean_text[final_start_index:].strip()
        # Remove trailing politeness
        real_title = re.sub(r"\s+(please|thanks|thank you)\W*$", "", real_title, flags=re.IGNORECASE)
        real_title = real_title.strip()
        
        # 5. Personalize Pronouns (I -> You, My -> Your)
        # Apply strict word boundary checks
        replacements = [
            (r"\bI'm\b", "You're"),
            (r"\bI\b", "You"),
            (r"\bmy\b", "your"),
            (r"\bMy\b", "Your"),
            (r"\bme\b", "you"),
            (r"\bam\b", "are"),
             # Optional: "myself" -> "yourself" handling if needed, but basic set covers 95%
        ]
        
        # Apply replacements to the title
        # We process matches case-insensitively for the search, but simple Sub works if we use flags.
        # However, `re.sub` needs to be done carefully to preserve original case if not matched,
        # but here we WANT to change the word.
        
        for pattern, replacement in replacements:
            real_title = re.sub(pattern, replacement, real_title, flags=re.IGNORECASE)
            
        if not real_title:
            # If we stripped everything, use original?
            real_title = "New Task"

        response["title"] = real_title.capitalize()
        response["is_complete"] = True
        
        # Friendly response text
        # Format extracted_date pretty
        pretty_time = extracted_date.strftime("%I:%M %p")
        
        if matches:
            response["response_text"] = f"Got it! Scheduled '{response['title']}' for {pretty_time}. ✅"
        else:
            # Auto +3h
            response["response_text"] = f"Added '{response['title']}'. Due at {pretty_time} (in 3 hrs). ✅"

        return response

    except Exception as e:
        logger.error(f"Logic Voice processing failed: {e}")
        return {
            "title": "",
            "time": None,
            "type": "task",
            "response_text": "I had trouble understanding that. Could you try again?",
            "is_complete": False
        }
