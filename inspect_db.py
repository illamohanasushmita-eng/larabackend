
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def inspect_db():
    async with engine.connect() as conn:
        for table in ['users', 'tasks', 'user_settings']:
            print(f"\n--- Table: {table} ---")
            result = await conn.execute(text(f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table}';
            """))
            for row in result:
                print(row)

if __name__ == "__main__":
    asyncio.run(inspect_db())
