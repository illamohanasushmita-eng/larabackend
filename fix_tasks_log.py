import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

async def fix_missing_columns():
    output = []
    output.append("🔍 Starting database fix...")
    
    async with engine.begin() as conn:
        try:
            # Get existing columns
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks';"
            ))
            existing_columns = [row[0] for row in result.fetchall()]
            output.append(f"Existing columns: {existing_columns}")

            expected = [
                ("raw_text", "VARCHAR"),
                ("description", "VARCHAR"),
                ("status", "VARCHAR"),
                ("type", "VARCHAR"),
                ("due_date", "TIMESTAMP WITH TIME ZONE"),
                ("end_time", "TIMESTAMP WITH TIME ZONE"),
                ("notified_10m", "BOOLEAN DEFAULT FALSE"),
                ("notified_20m", "BOOLEAN DEFAULT FALSE"),
                ("notified_due", "BOOLEAN DEFAULT FALSE"),
                ("notified_completion", "BOOLEAN DEFAULT FALSE"),
                ("notified_30m_post", "BOOLEAN DEFAULT FALSE"),
                ("last_nudged_at", "TIMESTAMP WITH TIME ZONE"),
                ("med_timing", "VARCHAR"),
                ("external_id", "VARCHAR"),
                ("is_external", "BOOLEAN DEFAULT FALSE")
            ]

            for col_name, col_type in expected:
                if col_name.lower() not in [c.lower() for c in existing_columns]:
                    output.append(f"➕ Adding missing column: {col_name}")
                    try:
                        await conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type};"))
                        output.append(f"   ✅ Added {col_name}")
                    except Exception as e:
                        output.append(f"   ❌ Error adding {col_name}: {e}")
                else:
                    output.append(f"ℹ️ Column '{col_name}' already exists.")

        except Exception as e:
            output.append(f"❌ Database error: {e}")

    output.append("\n✨ Database fix complete!")
    
    with open("fix_log.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    asyncio.run(fix_missing_columns())
