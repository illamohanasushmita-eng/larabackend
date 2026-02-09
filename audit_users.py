
import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.core.security import pwd_context

async def audit_passwords():
    async with engine.connect() as conn:
        print("\n🔍 [Audit] Checking user password hashes...")
        res = await conn.execute(text("SELECT id, email, hashed_password FROM users"))
        users = res.fetchall()
        
        invalid_users = []
        for user in users:
            uid, email, hp = user
            is_valid = False
            try:
                if hp:
                    # identify() returns the scheme if recognized, else None or raises error
                    scheme = pwd_context.identify(hp)
                    if scheme == "bcrypt":
                        is_valid = True
            except Exception:
                pass
            
            status = "✅ VALID" if is_valid else "❌ INVALID"
            print(f"User: {email} | Hash: {hp[:10]}... | Status: {status}")
            
            if not is_valid:
                invalid_users.append(uid)
        
        if invalid_users:
            print(f"\n⚠️ Found {len(invalid_users)} users with invalid hashes.")
            confirm = "yes" # In a real scenario I might ask, but here I'll just report.
            print("To fix this, you should delete these users or re-register them.")
        else:
            print("\n✅ All existing user hashes are valid bcrypt.")

if __name__ == "__main__":
    asyncio.run(audit_passwords())
