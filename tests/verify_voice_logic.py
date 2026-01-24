import httpx
import asyncio
import sys

# Windows loop policy workaround if needed
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_URL = "http://127.0.0.1:8000/api/v1/tasks"

async def verify_voice_logic():
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        # 1. Trimming Whitespace
        print("Test 1: Trimming Whitespace...")
        payload = {"title": "  Buy milk  ", "description": "  urgent  "}
        resp = await client.post(BASE_URL + "/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        if data["title"] == "Buy milk" and data["description"] == "urgent":
             print("PASS: Whitespace trimmed.")
        else:
             print(f"FAIL: Whitespace not trimmed. Got '{data['title']}'")

        # 2. Empty Title Rejection
        print("Test 2: Empty Title...")
        payload = {"title": "   ", "description": "should fail"}
        resp = await client.post(BASE_URL + "/", json=payload)
        if resp.status_code == 422:
             print("PASS: Empty title rejected.")
        else:
             print(f"FAIL: Empty title accepted? Status {resp.status_code}")

        # 3. Partial Date (Pydantic default parsing)
        # Note: Pydantic v2 requires full ISO or lenient parsing enabled?
        # Let's see what happens with YYYY-MM-DD
        print("Test 3: Date only (YYYY-MM-DD)...")
        payload = {"title": "Date Test", "due_date": "2026-05-20"}
        resp = await client.post(BASE_URL + "/", json=payload)
        if resp.status_code == 201:
             print(f"PASS: Date accepted. Got {resp.json()['due_date']}")
        else:
             print(f"FAIL: Date rejected. Status {resp.status_code} {resp.text}")

if __name__ == "__main__":
    asyncio.run(verify_voice_logic())
