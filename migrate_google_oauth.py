import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def update_database():
    """
    Update the Railway PostgreSQL database to include Google OAuth columns.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ Error: DATABASE_URL not found in .env file.")
        return

    # Railway URLs sometimes start with postgres://, but asyncpg needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to database...")
    
    try:
        # Connect to the database
        conn = await asyncpg.connect(database_url)
        
        print("Checking for users table...")
        
        # Add columns if they don't exist
        # We use a single DO block for cleaner execution
        await conn.execute("""
            DO $$ 
            BEGIN 
                -- Add google_access_token
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='users' AND COLUMN_NAME='google_access_token') THEN
                    ALTER TABLE users ADD COLUMN google_access_token VARCHAR;
                END IF;

                -- Add google_refresh_token
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='users' AND COLUMN_NAME='google_refresh_token') THEN
                    ALTER TABLE users ADD COLUMN google_refresh_token VARCHAR;
                END IF;

                -- Add google_token_expiry
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='users' AND COLUMN_NAME='google_token_expiry') THEN
                    ALTER TABLE users ADD COLUMN google_token_expiry TIMESTAMP;
                END IF;
            END $$;
        """)
        
        print("✅ SUCCESS: Database updated with Google OAuth columns!")
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")

if __name__ == "__main__":
    asyncio.run(update_database())
