import asyncio
import asyncpg
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings

async def create_database():
    """Create the PostgreSQL database if it doesn't exist."""
    try:
        # Connect to default postgres database to create our database
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database='postgres',
            host=settings.POSTGRES_SERVER
        )

        # Check if database exists
        result = await conn.fetchval("""
            SELECT 1 FROM pg_database WHERE datname = $1
        """, settings.POSTGRES_DB)

        if result:
            print(f"✅ Database '{settings.POSTGRES_DB}' already exists")
        else:
            # Create database
            await conn.execute(f'CREATE DATABASE {settings.POSTGRES_DB}')
            print(f"✅ Created database '{settings.POSTGRES_DB}'")

        await conn.close()

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print("💡 Make sure PostgreSQL is running and credentials are correct")
        return False

    return True

async def create_tables():
    """Create the tasks table in the database."""
    try:
        # Connect to our database
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_SERVER
        )

        # Create tasks table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id BIGSERIAL PRIMARY KEY,
                title VARCHAR NOT NULL,
                description TEXT,
                status VARCHAR DEFAULT 'pending',
                type VARCHAR DEFAULT 'task',
                due_date TIMESTAMP WITH TIME ZONE,
                user_id BIGINT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on status for better query performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)

        # Create index on type for filtering tasks vs reminders
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)
        """)

        print("✅ Created tables and indexes")
        await conn.close()

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

    return True

async def test_connection():
    """Test the database connection."""
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_SERVER
        )

        # Test query
        result = await conn.fetchval("SELECT COUNT(*) FROM tasks")
        print(f"✅ Database connection successful. Current tasks count: {result}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def main():
    print("Setting up PostgreSQL database for LARA Voice Assistant")
    print(f"Database: {settings.POSTGRES_DB}")
    print(f"Host: {settings.POSTGRES_SERVER}")
    print(f"User: {settings.POSTGRES_USER}")
    print()

    # Step 1: Create database
    if not await create_database():
        return

    # Step 2: Create tables
    if not await create_tables():
        return

    # Step 3: Test connection
    if await test_connection():
        print()
        print("PostgreSQL setup complete!")
        print("Your voice tasks will be stored in the 'lara_db.tasks' table")
        print()
        print("Table structure:")
        print("  - id (BIGSERIAL PRIMARY KEY)")
        print("  - title (VARCHAR)")
        print("  - description (TEXT)")
        print("  - status (VARCHAR, default 'pending')")
        print("  - type (VARCHAR, 'task' or 'reminder')")
        print("  - due_date (TIMESTAMP WITH TIME ZONE)")
        print("  - user_id (BIGINT)")
        print("  - created_at (TIMESTAMP WITH TIME ZONE)")
        print("  - updated_at (TIMESTAMP WITH TIME ZONE)")

if __name__ == "__main__":
    asyncio.run(main())
