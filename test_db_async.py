import asyncio
import sys
import os

# Add the project root to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

async def test_connection():
    """
    Simple async test to verify Supabase PostgreSQL connection
    """
    print("🚀 Starting Database Connection Test...")
    
    try:
        # Create a connection and execute SELECT 1
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            
            if val == 1:
                print("✅ SUCCESS: Database connection established! (Returned SELECT 1)")
            else:
                print(f"⚠️  UNEXPECTED: Connection worked but returned {val} instead of 1")
                
    except Exception as e:
        print("❌ ERROR: Failed to connect to the database.")
        print(f"Details: {str(e)}")
        
    finally:
        # Dispose engine resources
        await engine.dispose()
        print("🏁 Test finished.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        # Required for Windows async operations
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_connection())
