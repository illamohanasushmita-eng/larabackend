"""
Test script to send FCM notifications

Usage:
    python test_fcm.py
"""

import requests
import json

# Your backend URL
BASE_URL = "http://192.168.31.184:8000"  # Update if your IP changed
API_URL = f"{BASE_URL}/api/v1/notifications"

def test_basic_notification():
    """Send a basic test notification"""
    print("\n📤 Sending basic test notification...")
    
    response = requests.post(
        f"{API_URL}/test-notification/",
        json={
            "title": "Hello from LARA! 👋",
            "body": "This is a test notification from your AI assistant"
        }
    )
    
    if response.status_code == 200:
        print("✅ Success:", response.json())
    else:
        print("❌ Failed:", response.status_code, response.text)

def test_morning_summary():
    """Send a morning summary notification"""
    print("\n🌅 Sending morning summary notification...")
    
    response = requests.post(f"{API_URL}/morning-summary-test/")
    
    if response.status_code == 200:
        print("✅ Success:", response.json())
    else:
        print("❌ Failed:", response.status_code, response.text)

def test_evening_summary():
    """Send an evening summary notification"""
    print("\n🌙 Sending evening summary notification...")
    
    response = requests.post(f"{API_URL}/evening-summary-test/")
    
    if response.status_code == 200:
        print("✅ Success:", response.json())
    else:
        print("❌ Failed:", response.status_code, response.text)

if __name__ == "__main__":
    print("=" * 50)
    print("🔔 FCM Notification Test Script")
    print("=" * 50)
    
    print("\nMake sure:")
    print("1. Backend is running (uvicorn app.main:app --host 0.0.0.0 --port 8000)")
    print("2. Your phone has the app installed and opened at least once")
    print("3. FCM token is registered in the database")
    
    input("\nPress Enter to continue...")
    
    # Run tests
    test_basic_notification()
    test_morning_summary()
    test_evening_summary()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("=" * 50)
