from groq import Groq
from app.core.config import settings

# Initialize the Groq client only once
if settings.GROQ_API_KEY:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
else:
    # In production, you'd want to handle this more strictly
    groq_client = None

def get_groq_client():
    """Returns the initialized Groq client."""
    return groq_client
