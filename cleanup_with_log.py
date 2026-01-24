
import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.core.security import pwd_context
import sys

async def fix_invalid_users():
    with open("cleanup_log.txt", "w", encoding="utf-8") as f:
        print("Starting cleanup...", file=f)
        async with engine.connect() as conn:
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
                    f.write(f"❌ INVALID: {email}\n")
                    to_delete.append(uid)
                else:
                    f.write(f"✅ VALID: {email}\n")
            
            if to_delete:
                for uid in to_delete:
                    await conn.execute(text(f"DELETE FROM tasks WHERE user_id = {uid}"))
                    await conn.execute(text(f"DELETE FROM user_settings WHERE user_id = {uid}"))
                    await conn.execute(text(f"DELETE FROM users WHERE id = {uid}"))
                await conn.commit()
                f.write(f"✨ Deleted {len(to_delete)} invalid users.\n")
            else:
                f.write("🙌 No invalid users found.\n")

if __name__ == "__main__":
    asyncio.run(fix_invalid_users())
