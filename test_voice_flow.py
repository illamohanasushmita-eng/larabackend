"""
Test script for voice task flow - Multi-turn conversation support

This script simulates the voice assistant flow to verify the fix works correctly.
Run this after deploying the backend changes.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your Railway URL for production testing
API_ENDPOINT = f"{BASE_URL}/api/v1/tasks/process-voice"

def test_voice_flow(test_name: str, inputs: list[str], expected_statuses: list[str]):
    """
    Test a multi-turn voice conversation flow
    
    Args:
        test_name: Name of the test case
        inputs: List of user inputs (simulating voice transcripts)
        expected_statuses: Expected status after each input
    """
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    
    context = None  # Simulates pendingContext in frontend
    
    for i, (user_input, expected_status) in enumerate(zip(inputs, expected_statuses)):
        # Simulate frontend combining context with new input
        combined_input = f"{context} {user_input}" if context else user_input
        
        print(f"\n--- Turn {i+1} ---")
        print(f"User says: '{user_input}'")
        print(f"Sending to AI: '{combined_input}'")
        
        # Call the API
        payload = {
            "text": combined_input,
            "current_time": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload)
            response.raise_for_status()
            result = response.json()
            
            print(f"AI Status: {result['status']}")
            print(f"AI Title: {result['title']}")
            print(f"AI Sentence: {result['corrected_sentence']}")
            print(f"AI Time: {result.get('time', 'None')}")
            print(f"AI Message: {result['message']}")
            
            # Verify expected status
            if result['status'] == expected_status:
                print(f"✅ Status matches expected: {expected_status}")
            else:
                print(f"❌ Status mismatch! Expected: {expected_status}, Got: {result['status']}")
            
            # Update context for next turn
            if result['status'] == 'incomplete':
                context = result['corrected_sentence']
                print(f"📝 Storing context for next turn: '{context}'")
            else:
                context = None  # Clear context when ready/error
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return False
    
    print(f"\n{'='*60}")
    return True


def main():
    print("🎤 Voice Task Flow Test Suite")
    print("Testing multi-turn conversation support")
    
    # Test Case 1: Two-turn conversation (the main fix)
    test_voice_flow(
        test_name="Two-Turn: Task then Time",
        inputs=[
            "Remind me to meet my friends",
            "5 PM"
        ],
        expected_statuses=[
            "incomplete",  # First turn: task without time
            "ready"        # Second turn: combined with time
        ]
    )
    
    # Test Case 2: Single-turn with time included
    test_voice_flow(
        test_name="Single-Turn: Task with Time",
        inputs=[
            "Remind me to call mom at 6 PM"
        ],
        expected_statuses=[
            "ready"  # Should be ready immediately
        ]
    )
    
    # Test Case 3: Another two-turn example
    test_voice_flow(
        test_name="Two-Turn: Different Task",
        inputs=[
            "Call the dentist",
            "tomorrow at 3 PM"
        ],
        expected_statuses=[
            "incomplete",
            "ready"
        ]
    )
    
    # Test Case 4: Task with "at" preposition
    test_voice_flow(
        test_name="Single-Turn: With 'at' Preposition",
        inputs=[
            "Meeting at 2 PM"
        ],
        expected_statuses=[
            "ready"
        ]
    )
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
