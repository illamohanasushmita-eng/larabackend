import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_adaptive_logic():
    print("[TEST] Starting Adaptive AI Verification...", flush=True)
    print("-" * 30, flush=True)
    
    # Mock dependencies
    mock_db = MagicMock()
    user_id = 1
    
    # We need to mock get_user_insights to return specific momentum states
    with patch('app.services.ai_service.get_user_insights') as mock_insights, \
         patch('app.services.ai_service.get_groq_client') as mock_client_getter:
             
        # Setup Mock API Client to capture the prompt
        mock_client = MagicMock()
        mock_client_getter.return_value = mock_client
        mock_completion = MagicMock()
        
        # Mock the API response to avoid actual network call errors
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = '{"status": "ready", "title": "Test Task", "corrected_sentence": "Test", "time": null}'
        mock_client.chat.completions.create.return_value = mock_completion

        from app.services.ai_service import process_voice_command

        # TEST 1: Low Energy (16:00 / 4 PM), Low Momentum (Overwhelmed)
        print("Test Case 1: 4 PM (Afternoon Slump) + Low Momentum")
        mock_insights.return_value = {"completion_rate": 10, "overdue_tasks": 10} # Low momentum
        
        await process_voice_command("add task", mock_db, user_id, current_time="2026-02-05T16:00:00")
        
        # Capture calls
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        system_prompt = messages[0]['content']
        
        if "User Energy: Low (Afternoon Slump)" in system_prompt and "User Momentum: Low (Overwhelmed)" in system_prompt:
             print("[PASS] Correctly injected 'Afternoon Slump' and 'Overwhelmed' context.", flush=True)
        else:
             print("[FAIL] Context missing.", flush=True)
             print("DEBUG Prompt:", system_prompt[:500], flush=True)

        print("-" * 30, flush=True)

        # TEST 2: High Energy (9:00 / 9 AM), High Momentum (Crushing it)
        print("Test Case 2: 9 AM (Morning Freshness) + High Momentum")
        mock_insights.return_value = {"completion_rate": 80, "overdue_tasks": 0} # High momentum
        
        await process_voice_command("add task", mock_db, user_id, current_time="2026-02-05T09:00:00")
        
        # Capture calls
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        system_prompt = messages[0]['content']
        
        if "User Energy: High (Morning Freshness)" in system_prompt and "User Momentum: High (Crushing it)" in system_prompt:
             print("[PASS] Correctly injected 'Morning Freshness' and 'Crushing it' context.", flush=True)
        else:
             print("[FAIL] Context missing.", flush=True)
             print("DEBUG Prompt:", system_prompt[:500], flush=True)

if __name__ == "__main__":
    asyncio.run(test_adaptive_logic())
