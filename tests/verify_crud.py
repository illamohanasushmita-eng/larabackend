import httpx
import asyncio
import sys

# Windows loop policy workaround if needed
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_URL = "http://127.0.0.1:8000/api/v1/tasks"
ROOT_URL = "http://127.0.0.1:8000"

async def verify_crud():
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        # 0. Health Check
        print("Checking root endpoint...")
        try:
            resp = await client.get(ROOT_URL + "/")
            print(f"Root endpoint status: {resp.status_code}")
            print(f"Root response: {resp.json()}")
        except Exception as e:
            print(f"Health check failed: {e}")
            return

        # 1. Create
        print("Creating task...")
        payload = {"title": "Test Task", "description": "Testing CRUD"}
        resp = await client.post(BASE_URL + "/", json=payload)
        if resp.status_code != 201:
            print(f"Create failed: {resp.status_code} {resp.text}")
            return
        task = resp.json()
        task_id = task["id"]
        print(f"Created task: {task_id}")

        # 2. List
        print("Listing tasks...")
        resp = await client.get(BASE_URL + "/")
        assert resp.status_code == 200
        tasks = resp.json()
        assert any(t["id"] == task_id for t in tasks)
        print("Task found in list.")

        # 3. Get Detail
        print("Getting task detail...")
        resp = await client.get(f"{BASE_URL}/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Task"
        print("Task detail verified.")

        # 4. Update (PATCH)
        print("Updating task...")
        resp = await client.patch(f"{BASE_URL}/{task_id}", json={"status": "completed"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        print("Task updated.")

        # 5. Delete
        print("Deleting task...")
        resp = await client.delete(f"{BASE_URL}/{task_id}")
        assert resp.status_code == 200
        print("Task deleted.")

        # 6. Verify Deletion
        print("Verifying deletion...")
        resp = await client.get(f"{BASE_URL}/{task_id}")
        assert resp.status_code == 404
        print("Task correctly not found.")
        print("SUCCESS: Full CRUD verified.")

if __name__ == "__main__":
    asyncio.run(verify_crud())
