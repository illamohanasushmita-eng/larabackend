import asyncio
import asyncpg
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def get_postgres_credentials():
    """Get PostgreSQL credentials from user input."""
    print("PostgreSQL Setup for LARA Voice Assistant")
    print("==========================================")
    print()

    host = input("PostgreSQL Host (default: localhost): ").strip() or "localhost"
    user = input("PostgreSQL Username (default: postgres): ").strip() or "postgres"
    password = input("PostgreSQL Password: ").strip()
    database = input("Database Name (default: lara_db): ").strip() or "lara_db"

    return {
        "host": host,
        "user": user,
        "password": password,
        "database": database
    }

async def create_database(creds):
    """Create the PostgreSQL database if it doesn't exist."""
    try:
        # Connect to default postgres database to create our database
        conn = await asyncpg.connect(
            user=creds["user"],
            password=creds["password"],
            database='postgres',
            host=creds["host"]
        )

        # Check if database exists
        result = await conn.fetchval("""
            SELECT 1 FROM pg_database WHERE datname = $1
        """, creds["database"])

        if result:
            print(f"Database '{creds['database']}' already exists")
        else:
            # Create database
            await conn.execute(f'CREATE DATABASE {creds["database"]}')
            print(f"Created database '{creds['database']}'")

        await conn.close()
        return True

    except Exception as e:
        print(f"Error creating database: {e}")
        print("Make sure PostgreSQL is running and credentials are correct")
        return False

async def create_tables(creds):
    """Create the tasks table in the database."""
    try:
        # Connect to our database
        conn = await asyncpg.connect(
            user=creds["user"],
            password=creds["password"],
            database=creds["database"],
            host=creds["host"]
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

        print("Created tables and indexes")
        await conn.close()
        return True

    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

async def test_connection(creds):
    """Test the database connection."""
    try:
        conn = await asyncpg.connect(
            user=creds["user"],
            password=creds["password"],
            database=creds["database"],
            host=creds["host"]
        )

        # Test query
        result = await conn.fetchval("SELECT COUNT(*) FROM tasks")
        print(f"Database connection successful. Current tasks count: {result}")

        await conn.close()
        return True

    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def main():
    creds = get_postgres_credentials()

    # Step 1: Create database
    print("\nStep 1: Creating database...")
    if not await create_database(creds):
        return

    # Step 2: Create tables
    print("\nStep 2: Creating tables...")
    if not await create_tables(creds):
        return

    # Step 3: Test connection
    print("\nStep 3: Testing connection...")
    if await test_connection(creds):
        print("\nSUCCESS: PostgreSQL setup complete!")
        print(f"Your voice tasks will be stored in the '{creds['database']}.tasks' table")
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
        print()
        print("You can now start your backend server with:")
        print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    asyncio.run(main())
