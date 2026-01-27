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
                    "content": "You are a helpful, concise AI personal assistant. Provide short, clear, and natural-sounding responses suitable for voice interaction. Avoid using markdown formatting like bolding or bullet points unless absolutely necessary, as this will be read aloud."
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
