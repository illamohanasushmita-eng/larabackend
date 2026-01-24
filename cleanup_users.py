
import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.core.security import pwd_context

async def fix_invalid_users():
    async with engine.connect() as conn:
        print("\n🔍 [Fix] Starting database audit and fix...")
        res = await conn.execute(text("SELECT id, email, hashed_password FROM users"))
        users = res.fetchall()
        
        to_delete = []
        for user in users:
            uid, email, hp = user
            is_valid = False
            try:
                if hp:
                    scheme = pwd_context.identify(hp)
                    if scheme == "bcrypt":
                        is_valid = True
            except Exception:
                pass
            
            if not is_valid:
                # Check if it looks like plain text
                print(f"❌ Found invalid hash for: {email}")
                to_delete.append(uid)
            else:
                print(f"✅ Valid hash for: {email}")
        
        if to_delete:
            print(f"\n🗑️ Deleting {len(to_delete)} users with invalid passwords...")
            # Delete from dependencies first (cascade should handle but being safe)
            for uid in to_delete:
                await conn.execute(text(f"DELETE FROM tasks WHERE user_id = {uid}"))
                await conn.execute(text(f"DELETE FROM user_settings WHERE user_id = {uid}"))
                await conn.execute(text(f"DELETE FROM users WHERE id = {uid}"))
            await conn.commit()
            print("✨ Cleanup complete. Please re-register these users.")
        else:
            print("\n🙌 No invalid users found.")

if __name__ == "__main__":
    asyncio.run(fix_invalid_users())

