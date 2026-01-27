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

async def process_voice_command(text: str, current_time: str = None) -> dict:
    """
    Processes voice input to extract task details and generate an assistant response.
    Specifically focuses on ensuring a time is always provided, asking if missing.
    """
    client = get_groq_client()
    if not client:
        return {
            "success": False,
            "message": "I'm sorry, I cannot process your request right now.",
            "requires_user_input": False,
            "reason": "service_unavailable"
        }

    # Strict prompt for Time-First Assistant logic
    system_prompt = f"""You are LARA, a dedicated AI Personal Assistant.
Current Local Time: {current_time if current_time else 'Unknown'}

Your goal is to parse user input into a task/reminder with a TITLE and a TIME.
A TIME is mandatory for LARA to schedule anything.

EXTRACT RULES:
1. TITLE: Every request needs a title. If the user only says a time (e.g. "at 5 PM"), use "Pending Task" as the title.
2. TIME: If a specific time is mentioned, extract it as an ISO 8601 string.
3. MISSING TIME: If the user provides a task but NO time, you MUST set 'requires_user_input' to true and ask: "Sure. At what time should I set this reminder (IST)?"
4. COMPLETE: If both are present, confirm clearly: "Got it. I will remind you to <title> at <time> IST."

Return ONLY a JSON object:
{{
  "success": true,
  "title": string,
  "time": string (ISO 8601) or null,
  "type": "task" or "reminder",
  "message": string (Spoken response),
  "requires_user_input": boolean,
  "reason": "missing_time" | "complete"
}}

Example:
Input: "Remind me to call dad"
Output: {{"success": true, "title": "Call dad", "time": null, "type": "reminder", "message": "Sure. At what time should I set this reminder (IST)?", "requires_user_input": true, "reason": "missing_time"}}"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(chat_completion.choices[0].message.content)
        
        return {
            "success": result.get("success", False),
            "title": result.get("title"),
            "time": result.get("time"),
            "type": result.get("type", "task"),
            "message": result.get("message", "I've noted that."),
            "requires_user_input": result.get("requires_user_input", False),
            "reason": result.get("reason"),
            "is_cancelled": False
        }
    except Exception as e:
        logger.error(f"Error processing voice command: {str(e)}")
        return {
            "success": False,
            "message": "I didn't quite catch that. Could you repeat?",
            "requires_user_input": True,
            "reason": "parsing_error"
        }





