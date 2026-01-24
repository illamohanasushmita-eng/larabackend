import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def create_notifications_table():
    """
    Create the notifications table manually.
    """
    print("🔍 Creating notifications table...")
    
    async with engine.begin() as conn:
        try:
            print("🧱 Creating table 'notifications'...")
            sql = """
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR,
                body VARCHAR,
                data TEXT, -- will store JSON string
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications (id);
            CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
            """
            await conn.execute(text(sql))
            print("✅ Notifications table and indexes created successfully.")
        except Exception as e:
            print(f"❌ Error creating notifications table: {e}")

    print("✨ Database update complete!")

if __name__ == "__main__":
    asyncio.run(create_notifications_table())
