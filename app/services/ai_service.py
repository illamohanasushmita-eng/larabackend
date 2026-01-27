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
    Processes voice input with conversational intelligence.
    Returns grammar-enhanced text and structured task details.
    """
    client = get_groq_client()
    if not client:
        return {
            "success": False,
            "corrected_sentence": text,
            "message": "I'm having trouble connecting to my brain. Please check the API configuration.",
            "requires_user_input": False,
            "reason": "service_unavailable"
        }

    system_prompt = f"""You are LARA, a smart AI Personal Assistant.
Current Local Time: {current_time if current_time else 'Unknown'}

Follow these steps exactly for every user input:

STEP 1: Sentence Formation
- Rewrite the user's input into a perfect, natural English sentence. Extract this as 'corrected_sentence'. Keep the meaning identical.

STEP 2: Detect Intent
- Determine if the user wants to add a task, set a reminder, or just talk.

STEP 3: Extraction
- Extract 'title' and 'time' (as ISO 8601 string).
- If 'time' is missing but they want a reminder/task, set 'requires_user_input' to true.

STEP 4: Response
- If missing time, 'message' should be: "Sure. At what time should I set this reminder (IST)?"
- If complete, 'message' should be: "Got it. I'll remind you to <title> at <time> IST."

Return ONLY a JSON object:
{{
  "success": boolean,
  "title": string or null,
  "corrected_sentence": string,
  "time": string (ISO 8601) or null,
  "type": "task" or "reminder",
  "message": string,
  "requires_user_input": boolean,
  "reason": "missing_time" | "complete" | "irrelevant"
}}"""

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
        
        # 🛡️ PRODUCTION SAFETY: Guarantee non-nullable str for 'type'
        # Prevent 'ResponseValidationError: Input should be a valid string'
        raw_type = result.get("type", "task")
        final_type = str(raw_type) if raw_type is not None else "task"

        return {
            "success": result.get("success", True),
            "title": result.get("title"),
            "corrected_sentence": result.get("corrected_sentence", text),
            "time": result.get("time"),
            "type": final_type,
            "message": result.get("message", "Processing..."),
            "requires_user_input": result.get("requires_user_input", False),
            "reason": result.get("reason"),
            "is_cancelled": False
        }
    except Exception as e:
        logger.error(f"Error processing voice command: {str(e)}")
        return {
            "success": False,
            "corrected_sentence": text,
            "message": f"I encountered an error: {str(e)}",
            "requires_user_input": True,
            "reason": "parsing_error"
        }







