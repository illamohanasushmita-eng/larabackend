import logging
import re
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

# --- NO GEMINI ---
# Pure logic-based parsing to ensure stability

async def generate_ai_summary(summary_type: str, user_name: str, tasks: list):
    """
    Generate a formatted summary using templates instead of AI
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
    Logic-based voice parser (Regex)
    Extracts 'Time' and 'Title' from natural language
    """
    try:
        user_text_lower = user_text.lower()
        
        # 1. Defaults
        response = {
            "title": "",
            "time": None,
            "type": "task",
            "is_complete": False,
            "response_text": ""
        }

        # 2. Extract Time using Regex
        # Matches: "at 5 pm", "at 10:30", "at 7"
        time_match = re.search(r'\bat\s+(\d{1,2})(:(\d{2}))?\s*(am|pm)?', user_text_lower)
        extracted_time = None
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(3)) if time_match.group(3) else 0
            period = time_match.group(4) # am/pm

            # Convert to 24-hour HH:MM
            if period:
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            
            extracted_time = f"{hour:02d}:{minute:02d}"
            
            # Remove the time string from the title
            # Clean "at 5 pm" from text
            clean_text = re.sub(r'\bat\s+(\d{1,2})(:(\d{2}))?\s*(am|pm)?', '', user_text, flags=re.IGNORECASE)
        else:
            clean_text = user_text

        # 3. Clean Title & Verb Extraction
        # Strategy: Look for common task verbs. If found, start title from there.
        # If no verb found, stick to prefix removal or raw text.
        
        common_verbs = [
            "buy", "get", "purchase", "order",
            "call", "contact", "email", "message", "text", "whatsapp",
            "meet", "schedule", "attend", "join",
            "pay", "transfer", "send",
            "clean", "wash", "fix", "repair",
            "finish", "submit", "complete", "do",
            "read", "write", "study", "learn",
            "visit", "go",
            "remind", "nudge", "wake"
        ]
        
        # Construct dynamic regex for verbs: \b(buy|call|meet...)\b
        verb_pattern = r"\b(" + "|".join(common_verbs) + r")\b"
        
        verb_match = re.search(verb_pattern, clean_text, re.IGNORECASE)
        
        if verb_match:
            # We found a strong verb!
            # If the verb is "remind" or "nudge", we usually want what comes AFTER "remind me to..."
            # For other verbs like "Buy milk", we want "Buy milk"
            
            verb = verb_match.group(1).lower()
            
            if verb in ["remind", "nudge", "wake"]:
                # Special handling: "Remind me to [Real Task]"
                # Look for "to" after the verb
                after_verb = clean_text[verb_match.end():]
                to_match = re.search(r"\bto\b", after_verb, re.IGNORECASE)
                if to_match:
                    clean_text = after_verb[to_match.end():].strip()
                else:
                    # Fallback "Remind mom"
                    clean_text = clean_text.strip()
            else:
                # Standard Action: "Buy milk..." -> take from verb onwards
                clean_text = clean_text[verb_match.start():].strip()
                
        else:
            # No strong verb found, fallback to prefix cleaning logic
            command_patterns = [
                r"add\s+a\s+task\s+to\s+",
                r"add\s+task\s+to\s+",
                r"create\s+a\s+task\s+to\s+",
                r"make\s+a\s+task\s+to\s+",
                r"new\s+task\s+"
            ]
            for pattern in command_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    clean_text = clean_text[match.end():].strip()
                    break
        
        # If no specific command phrase found, we assume the whole text is the title (minus time)
        clean_text = clean_text.strip()
        response["title"] = clean_text.capitalize()
        response["time"] = extracted_time

        # 4. Generate Response
        # 4. Generate Response
        if response["title"] and not response["time"]:
            # ✅ User Request: Restore One-Shot Logic
            # If no time mentioned, default to +3 hours from now
            now = datetime.now()
            default_due = now + timedelta(hours=3)
            extracted_time = default_due.strftime("%H:%M")
            
            response["time"] = extracted_time
            response["is_complete"] = True
            response["response_text"] = f"Got it! I've added '{response['title']}' for {extracted_time} (3 hours from now). ✅"
            
        elif response["title"] and response["time"]:
            # Complete
            response["is_complete"] = True
            response["response_text"] = f"Got it! I've scheduled '{response['title']}' for {extracted_time}. ✅"
            
        else:
            # Fallback
            response["response_text"] = "I didn't capture a task title. Could you say it again?"

        return response

    except Exception as e:
        logger.error(f"Logic Voice processing failed: {e}")
        return {
            "title": "",
            "time": None,
            "type": "task",
            "response_text": "I had a glitch processing that. One more time?",
            "is_complete": False
        }

