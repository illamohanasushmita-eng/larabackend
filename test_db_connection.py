import asyncio
import asyncpg
from datetime import datetime

# Connection details from your request
DB_CONFIG = {
    'user': 'postgre',
    'password': 'postgre',
    'database': 'lara_db',
    'host': 'localhost',
    'port': '5432'
}

async def test_connection():
    print("Testing connection to PostgreSQL...")
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL!")
        
        # Create a table if not exists (simulating what alembic does if it failed)
        # But we really want to checks if tasks table exists from alembic
        try:
            row = await conn.fetchrow("SELECT count(*) FROM tasks;")
            print(f"✅ 'tasks' table exists! Current task count: {row['count']}")
        except asyncpg.UndefinedTableError:
            print("❌ 'tasks' table does not exist. Migrations might not have run.")
            return

        # Insert a test voice task
        print("Attempting to insert a test voice task...")
        task_title = "Test Voice Task " + str(datetime.now())
        await conn.execute('''
            INSERT INTO tasks (title, type, status, created_at, updated_at)
            VALUES ($1, 'task', 'pending', NOW(), NOW())
        ''', task_title)
        print(f"✅ Successfully inserted task: {task_title}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
