import asyncio
import httpx
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings

async def test_rest_api():
    token = settings.MAPPLS_ACCESS_TOKEN
    print(f"[TEST] Token: {token}", flush=True)
    
    # URL for REST API Key
    # https://apis.mapmyindia.com/advancedmaps/v1/<key>/nearby_search/json
    url = f"https://apis.mapmyindia.com/advancedmaps/v1/{token}/nearby_search/json"
    
    lat = 12.9716
    lng = 77.5946
    query = "hospital"
    
    params = {
        "keywords": query,
        "refLocation": f"{lat},{lng}"
    }
    
    print(f"[TEST] Calling URL: {url} with params {params}", flush=True)
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            print(f"[INFO] Status: {resp.status_code}", flush=True)
            print(f"[INFO] Response: {resp.text[:500]}", flush=True)
        except Exception as e:
            print(f"[FAIL] Exception: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(test_rest_api())
