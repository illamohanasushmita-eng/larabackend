
import asyncio
import httpx

async def verify_auth():
    base_url = "http://localhost:8000/api/v1"
    email = "test_auth_verify@example.com"
    password = "testpassword123"
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        print("Registering...")
        reg_res = await client.post(f"{base_url}/users/register", json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        })
        print(f"Register Status: {reg_res.status_code}")
        if reg_res.status_code != 200 and "already exists" not in reg_res.text:
            print(f"Error: {reg_res.text}")
        
        # 2. Login
        print("Logging in...")
        login_res = await client.post(f"{base_url}/users/login", json={
            "email": email,
            "password": password
        })
        print(f"Login Status: {login_res.status_code}")
        if login_res.status_code != 200:
            print(f"Error: {login_res.text}")
            return
            
        token = login_res.json()["access_token"]
        print(f"Token received! Prefix: {token[:10]}...")
        
        # 3. Access protected endpoint
        print("Accessing protected /settings/...")
        headers = {"Authorization": f"Bearer {token}"}
        settings_res = await client.get(f"{base_url}/settings/", headers=headers)
        print(f"Settings Status: {settings_res.status_code}")
        if settings_res.status_code == 200:
            print("✅ AUTH FLOW VERIFIED!")
        else:
            print(f"❌ AUTH FLOW FAILED: {settings_res.text}")

if __name__ == "__main__":
    try:
        asyncio.run(verify_auth())
    except Exception as e:
        print(f"Verification script error: {e}")
