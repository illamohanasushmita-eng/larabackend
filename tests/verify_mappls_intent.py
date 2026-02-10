
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services import ai_service
from app.core.database import AsyncSessionLocal

async def main():
    inputs = [
        "find nearby restaurants",
        "restaurants near me",
        "i want to eat something nearby",
        "search for hospitals",
        "where is the nearest gas station"
    ]
    
    # Mock DB session (not needed for this specific test but required by signature)
    async with AsyncSessionLocal() as db:
        for text in inputs:
            print(f"\nTesting input: '{text}'")
            result = await ai_service.process_voice_command(text, db, 1, "2024-02-10T10:00:00")
            print(f"Result: Intent={result.get('intent')}, Category={result.get('category')}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
