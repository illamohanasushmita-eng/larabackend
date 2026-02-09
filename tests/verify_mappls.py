import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_mappls_integration():
    print("[TEST] Starting Mappls Integration Verification...", flush=True)
    print("-" * 30, flush=True)
    
    # Mock dependencies
    mock_db = MagicMock()
    user_id = 1
    
    # 1. Test MapplsService.search_nearby logic (Mock API) & Formatting
    with patch('app.services.mappls_service.httpx.AsyncClient') as mock_client, \
         patch('app.services.mappls_service.settings') as mock_settings:
        
        mock_settings.MAPPLS_ACCESS_TOKEN = "dummy_token"
        
        # Setup Http Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestedLocations": [
                {"placeName": "City Hospital", "placeAddress": "Main St", "distance": 500},
                {"placeName": "General Clinic", "placeAddress": "2nd Ave", "distance": 1200}
            ]
        }
        # Correctly mock the async context manager + awaitable get
        mock_instance = mock_client.return_value
        mock_instance.__aenter__.return_value.get.return_value = mock_response

        from app.services.mappls_service import MapplsService
        
        print("[TEST] 1. Testing MapplsService.search_nearby...", flush=True)
        results = await MapplsService.search_nearby("hospital", 12.9716, 77.5946)
        
        if len(results) == 2 and results[0]["placeName"] == "City Hospital":
            print("[PASS] Service returned correct mock data.", flush=True)
        else:
            print(f"[FAIL] Service returned: {len(results)} items.", flush=True)

        print("-" * 30, flush=True)

        # 2. Test Formatting
        print("[TEST] 2. Testing Response Formatting...", flush=True)
        fmt = MapplsService.format_places_response(results, "hospital")
        if "City Hospital (500 meters away)" in fmt and "1.2 km away" in fmt:
            print(f"[PASS] Formatting check passed: '{fmt}'", flush=True)
        else:
            print(f"[FAIL] Formatting check failed: '{fmt}'", flush=True)

    print("-" * 30, flush=True)

    # 3. Test AI Intent logic (Mock AI output)
    print("[TEST] 3. Testing AI Intent Injection...", flush=True)
    
    with patch('app.services.ai_service.get_groq_client') as mock_groq, \
         patch('app.services.ai_service.get_user_insights') as mock_insights:
        
        mock_chat = MagicMock()
        mock_groq.return_value.chat.completions.create.return_value = mock_chat
        
        # Simulate AI identifying 'NearbySearch'
        mock_chat.choices = [MagicMock()]
        mock_chat.choices[0].message.content = '{"status": "ready", "intent": "NearbySearch", "category": "restaurant", "title": "Find Food"}'
        
        mock_insights.return_value = {} # Mock DB insights
        
        from app.services.ai_service import process_voice_command
        
        res = await process_voice_command("find restaurants", mock_db, user_id, current_time="2026-02-09T10:00:00")
        
        if res.get("intent") == "NearbySearch" and res.get("category") == "restaurant":
             print("[PASS] AI correctly identified NearbySearch intent.", flush=True)
        else:
             print(f"[FAIL] AI Output: {res}", flush=True)

if __name__ == "__main__":
    asyncio.run(test_mappls_integration())
