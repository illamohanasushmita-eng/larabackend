import asyncio
import asyncpg
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings

async def test_connection():
    print("Testing PostgreSQL connection...")
    print(f"Host: {settings.POSTGRES_SERVER}")
    print(f"Database: {settings.POSTGRES_DB}")
    print(f"User: {settings.POSTGRES_USER}")

    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_SERVER
        )

        # Test basic query
        result = await conn.fetchval("SELECT COUNT(*) FROM tasks")
        print(f"✅ Connection successful! Tasks count: {result}")

        # Test table structure
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position
        """)

        print("\n📊 Tasks table structure:")
        for row in result:
            print(f"  {row['column_name']} ({row['data_type']}) {'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your PostgreSQL credentials")
        print("3. Verify the 'lara_db' database exists")
        print("4. Ensure the 'tasks' table was created in pgAdmin")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
