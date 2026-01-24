"""
Quick script to check if FCM token is registered
"""

import requests

BASE_URL = "http://192.168.31.184:8000"

print("🔍 Checking FCM token registration...")
print("=" * 50)

response = requests.get(f"{BASE_URL}/api/v1/settings/")

if response.status_code == 200:
    data = response.json()
    print("\n✅ Settings retrieved successfully!")
    print(f"\nUser ID: {data.get('user_id')}")
    print(f"Morning Enabled: {data.get('morning_enabled')}")
    print(f"Evening Enabled: {data.get('evening_enabled')}")
    
    fcm_token = data.get('fcm_token')
    if fcm_token:
        print(f"\n✅ FCM Token: {fcm_token[:50]}... (truncated)")
        print("\n🎉 Token is registered! You can send notifications.")
    else:
        print("\n❌ FCM Token: None")
        print("\n⚠️  Token not registered yet!")
        print("\nTo fix this:")
        print("1. Install Firebase packages: npm install @react-native-firebase/app @react-native-firebase/messaging")
        print("2. Rebuild the app: npx expo prebuild --platform android --clean")
        print("3. Build APK: cd android && gradlew assembleRelease")
        print("4. Install the new APK on your phone")
        print("5. Open the app (it will auto-register the token)")
else:
    print(f"\n❌ Failed to get settings: {response.status_code}")
    print(response.text)

print("\n" + "=" * 50)
