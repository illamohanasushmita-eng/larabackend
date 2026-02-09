from fastapi import APIRouter, Query, HTTPException
from app.services.ai_service import ask_ai
from pydantic import BaseModel

router = APIRouter()

class AIResponse(BaseModel):
    prompt: str
    response: str

@router.get("/ai-response", response_model=AIResponse)
async def get_ai_response(prompt: str = Query(..., description="The user prompt to send to the AI")):
    """
    Calls ask_ai() with the provided prompt and returns a structured JSON response.
    """
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
    response_text = await ask_ai(prompt)
    
    return AIResponse(
        prompt=prompt,
        response=response_text
    )
