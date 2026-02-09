import asyncio
from sqlalchemy import text
from app.core.database import engine

async def create_users_table():
    async with engine.begin() as conn:
        print("Creating users table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR,
                email VARCHAR UNIQUE,
                hashed_password VARCHAR,
                is_active BOOLEAN DEFAULT TRUE
            );
            CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
            CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
        """))
        print("Table 'users' created successfully.")

if __name__ == "__main__":
    asyncio.run(create_users_table())
