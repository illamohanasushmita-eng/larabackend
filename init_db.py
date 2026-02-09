import asyncio
import sys
import os

# Add the current directory to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models import task, user_setting, user, notification

async def init_db():
    print("Starting Database Initialization...", flush=True)
    
    try:
        async with engine.begin() as conn:
            # Import models to ensure they are registered with Base.metadata
            print("Registering models...", flush=True)
            
            # This handles table creation based on the SQLAlchemy models
            print("Creating tables in PostgreSQL...", flush=True)
            await conn.run_sync(Base.metadata.create_all)
            
        print("SUCCESS: All tables created successfully!", flush=True)
        
        # Test connection
        print("Testing connection...", flush=True)
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            row = result.fetchone()
            print(f"Database Version: {row[0]}", flush=True)
            
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}", flush=True)
        if "ssl" in str(e).lower():
            print("Hint: If using Supabase/Railway, ensure SSL is required in your connection string or settings.", flush=True)

if __name__ == "__main__":
    asyncio.run(init_db())
