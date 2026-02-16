
import asyncio
import sys
import os

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.mappls_service import MapplsService
from app.core.config import settings

async def test_auth_and_search():
    print("🔄 Testing Mappls Auth...")
    
    # Force reset token
    MapplsService._access_token = None
    
    # 1. Test Token Generation
    token = await MapplsService.get_token()
    
    if token:
        print(f"✅ Token Generated: {token[:15]}...")
    else:
        print("❌ Failed to generate token! Check Client ID/Secret.")
        return

    # 2. Test Search (Restaurants)
    print("\n🔄 Testing Nearby Search (Restaurants)...")
    # Mumbai coordinates
    lat, lng = 19.0760, 72.8777
    results = await MapplsService.search_nearby("restaurants", lat, lng)
    
    if results:
        print(f"✅ Found {len(results)} places:")
        for p in results[:3]:
            print(f"   - {p.get('placeName')} ({p.get('distance')}m)")
    else:
        print("⚠️ No results found or API error.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_auth_and_search())
