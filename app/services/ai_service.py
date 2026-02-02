from app.core.groq_client import get_groq_client
import logging

logger = logging.getLogger(__name__)

async def ask_ai(prompt: str) -> str:
    """
    Sends user input to the Groq model llama-3.1-8b-instant
    Returns a clean, plain-text AI response
    """
    client = get_groq_client()
    
    if not client:
        logger.error("Groq client not initialized. Check GROQ_API_KEY in .env")
        return "I'm sorry, but I'm having trouble connecting to my brain right now. Please check my configuration."

    try:
        # Using llama-3.1-8b-instant as requested
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a voice-based AI Personal Assistant.
Your main responsibility is to convert spoken user input into clear, natural English sentences and respond like a smart assistant.
The user may speak in broken English, incomplete phrases, or short commands.

Follow these steps exactly:

STEP 1: Sentence Formation
- Rewrite the user’s spoken message into a grammatically correct, natural English sentence.
- Keep the same meaning.
- Do NOT add extra information.

STEP 2: Detect User Intent
Check if the user is trying to:
1. Add a task
2. Set a reminder
3. Ask a question
4. Request daily planning
5. General conversation

STEP 3: Task/Reminder Confirmation
If the user wants to add a task or reminder:
A. Extract:
   - Task title
   - Date (today/tomorrow/etc.)
   - Time (if provided)
B. If time is missing, ask clearly:
   "Sure. At what time should I set this reminder (IST)?"
C. If time is provided, confirm:
   "Got it. I will remind you to <task> at <time> IST."

STEP 4: Assistant Response Style
- Responses must be short, clear, and voice-friendly.
- Always sound polite and supportive.
- Avoid long paragraphs.
- Always use Indian Standard Time (IST).

STEP 5: Output Format (Always)
Return your response in exactly this format:
Corrected Sentence: <fixed user sentence>
Assistant Reply: <assistant response>"""
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
        )
        
        # Extract the content from the response
        response_text = chat_completion.choices[0].message.content
        return response_text.strip()
        
    except Exception as e:
        logger.error(f"Error calling Groq API: {str(e)}")
        return f"I encountered an error while processing your request: {str(e)}"

async def generate_ai_summary(summary_type: str, user_name: str, tasks: list) -> str:
    """
    Generates a daily summary (Morning/Evening) based on user's tasks.
    """
    client = get_groq_client()
    if not client:
        return ""

    # Format tasks for the prompt
    task_list_str = ""
    if tasks:
        for i, task in enumerate(tasks, 1):
            time_str = "No time set"
            if task.due_date:
                # Format to IST time for the prompt
                from datetime import timedelta
                ist_time = task.due_date + timedelta(hours=5, minutes=30)
                time_str = ist_time.strftime("%I:%M %p")
            task_list_str += f"{i}. {task.title} (at {time_str})\n"
    else:
        task_list_str = "No tasks scheduled for today."

    if summary_type == "MORNING":
        system_prompt = f"You are LARA, a cheerful and supportive AI assistant. It's morning. Greet {user_name} and give them a brief, motivating summary of their tasks for today. Keep it short and friendly for a push notification."
        user_prompt = f"Here are my tasks for today:\n{task_list_str}\n\nCan you give me a quick morning summary?"
    else:
        system_prompt = f"You are LARA, a polite AI assistant. It's evening. provide {user_name} a brief wrap-up of their day or a quick look at what's left. Keep it encouraging and very concise."
        user_prompt = f"Here are my tasks for today:\n{task_list_str}\n\nCan you give me a quick evening summary?"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating AI summary: {str(e)}")
        return "You have some tasks scheduled for today. Have a productive day!" if summary_type == "MORNING" else "Hope you had a productive day!"

async def generate_friendly_reminder(title: str, due_time: str, lead_mins: int) -> str:
    """
    Generate a friendly reminder message using Groq.
    - lead_mins: 20, 10, or 0 (Due Now)
    """
    client = get_groq_client()
    if not client:
        return f"Reminder: {title} at {due_time}"

    if lead_mins == 20:
        time_msg = "in 20 minutes"
    elif lead_mins == 10:
        time_msg = "in 10 minutes"
    else:
        time_msg = "right now"

    system_prompt = (
        "You are LARA, a cheerful and supportive AI personal assistant. "
        "Create a VERY SHORT, one-sentence friendly reminder for a push notification. "
        "IMPORTANT: You MUST use the exact time duration provided (e.g., '10 minutes') if you mention a duration. "
        "Do not change or hallucinate a different duration."
    )
    user_prompt = f"The task is '{title}' and it's due {time_msg} (at {due_time}). Phrase it nicely with an emoji."
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=60,
            temperature=0.3 # Lower temperature for higher accuracy
        )
        ai_response = chat_completion.choices[0].message.content.strip()
        
        # 🛡️ Safety check: If AI hallucinates '20' for a '10' minute lead, or vice-versa, correct it.
        if lead_mins == 10 and "20" in ai_response and "10" not in ai_response:
             ai_response = ai_response.replace("20", "10")
        elif lead_mins == 20 and "10" in ai_response and "20" not in ai_response:
             ai_response = ai_response.replace("10", "20")

        return ai_response
    except Exception as e:
        logger.error(f"Error generating AI reminder: {str(e)}")
        return f"Friendly reminder: {title} at {due_time}!"

async def process_voice_command(text: str, current_time: str = None) -> dict:
    """
    Assistant Lifecycle Processing:
    idle -> incomplete -> ready
    """
    client = get_groq_client()
    if not client:
        return {
            "status": "error",
            "title": "Service Error",
            "corrected_sentence": text,
            "message": "Service unavailable.",
            "is_cancelled": False
        }

    # Strict multi-stage prompt for Grammar & Intent
    system_prompt = f"""You are LARA, a professional AI Personal Assistant.
Current Local Time: {current_time if current_time else 'Unknown'}

CORE MISSION:
1. GRAMMAR & TITLE ENHANCEMENT:
   - **FIX BROKEN GRAMMAR**: Voice input is often broken or contains phonetic errors (e.g., "i meeting", "i call", "mee my friends" -> "meet my friends"). You MUST fix these into polished English.
   - **EXTRACT CONCISE TITLE**: The 'title' should be the core action ONLY. 
     - STRIP auxiliary phrases: "add task to", "remind me to", "i need to", "please", "can you", "i have to".
     - Example: "remind me to call my mom tomorrow" -> Title: "Call Mom"
     - Example: "add task to meet my friends" -> Title: "Meet Friends"
   - **SECOND PERSON PERSPECTIVE (MANDATORY)**: In the `corrected_sentence`, convert user's 1st person speech into 2nd person.
     - "I" -> "You"
     - "my" -> "your"
     - "me" -> "you"
   - **PROFESSIONAL PHRASING**: Ensure the output sounds like a professional assistant wrote it.

2. EXTRACTION: Identify the 'title', 'time' (ISO 8601 start time), and 'end_time' (ISO 8601 if provided).
   - **FUTURE TIME ONLY**: Your extracted time MUST always be in the future relative to the Current Local Time. If the user specifies a time that has already passed today, automatically move the date to tomorrow.
   - **MEETINGS/DURATION**: If the user mentions a meeting with a start and end time (e.g. "2 to 3 PM", "from 10 AM for 1 hour"), extract BOTH 'time' and 'end_time'.

Return ONLY a JSON object based on these examples:

Example 1:
Input: "remind me to call my mom tomorrow morning 5 o clock"
Output: {{
  "status": "ready",
  "title": "Call Mom",
  "corrected_sentence": "You have a reminder to call your mom tomorrow at 5:00 AM.",
  "time": "2026-01-29T05:00:00",
  "end_time": null,
  "type": "reminder",
  "message": "Got it. I've set a reminder to call your mom for tomorrow morning at 5 AM."
}}

Example 2:
Input: "meeting with boss today from 2 PM to 3:30 PM"
Output: {{
  "status": "ready",
  "title": "Meeting with Boss",
  "corrected_sentence": "You have a meeting with your boss today from 2:00 PM to 3:30 PM.",
  "time": "2026-01-28T14:00:00",
  "end_time": "2026-01-28T15:30:00",
  "type": "task",
  "message": "Alright. I've scheduled your meeting with your boss from 2:00 PM to 3:30 PM today."
}}

Return ONLY a JSON object:
{{
  "status": "ready" | "incomplete",
  "title": "Clean Short Title",
  "corrected_sentence": "Full polished sentence in 2nd person",
  "time": "ISO 8601 string or null",
  "end_time": "ISO 8601 string or null",
  "type": "task" or "reminder",
  "message": "Spoken assistant response"
}}"""

    try:
        logger.info(f"🎤 [AI Input] Processing: '{text}'")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Input: {text}"}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(chat_completion.choices[0].message.content)
        logger.info(f"🤖 [AI Output] Status: {result.get('status')}, Title: {result.get('title')}, Sentence: {result.get('corrected_sentence')}, Time: {result.get('time')}")
        
        # Production Safety: Cast values and handle defaults
        status = str(result.get("status", "incomplete"))
        title = str(result.get("title", "New Task")).strip() or "New Task"
        corrected = str(result.get("corrected_sentence", text)).strip() or text
        
        # 🛡️ SAFETY CHECK: If status is "ready" but no time was extracted, force incomplete
        if status == "ready" and not result.get("time"):
            logger.warning(f"⚠️ AI returned 'ready' but no time found. Forcing incomplete state.")
            status = "incomplete"
            result["message"] = "At what time should I set this reminder?"
        
        return {
            "status": status,
            "title": title,
            "corrected_sentence": corrected,
            "time": result.get("time"),
            "end_time": result.get("end_time"),
            "type": str(result.get("type", "task")),
            "message": str(result.get("message", "Processing...")),
            "is_cancelled": False
        }
    except Exception as e:
        logger.error(f"❌ AI Parsing Error: {str(e)}")
        return {
            "status": "error",
            "title": "Parsing Error",
            "corrected_sentence": text,
            "message": "I had trouble processing that. Can you repeat it?",
            "is_cancelled": False
        }









