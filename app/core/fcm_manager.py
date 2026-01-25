import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
import os

class FCMManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FCMManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            FCMManager._initialized = True

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK once with ENV or JSON file"""
        # 1. Prevent duplicate initialization
        if firebase_admin._apps:
            return

        try:
            # 2. Try initializing from Environment Variable (Railway/Production)
            if settings.FIREBASE_SERVICE_ACCOUNT:
                try:
                    import json
                    cred_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    print("✅ Firebase Admin SDK initialized from ENV")
                    return
                except Exception as e:
                    print(f"⚠️ Failed to parse FIREBASE_SERVICE_ACCOUNT JSON: {e}")
                    # Fall through to file method

            # 3. Fallback to Local JSON File (Development)
            cred_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "..", 
                settings.FIREBASE_CREDENTIALS
            )
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized from local file")
            else:
                print(f"⚠️ FIREBASE_SERVICE_ACCOUNT missing in Railway Variables and file not found at {cred_path}")
                
        except Exception as e:
            print(f"❌ CRITICAL: Failed to initialize Firebase: {e}")

    async def send_notification(self, token: str, title: str, body: str, data: dict = None, click_action: str = None):
        """
        Send a push notification to a specific device token (Async)
        """
        if not token:
            print("⚠️ No FCM token provided")
            return None

        try:
            # Prepare android and apns config for click actions
            # We use 'fcm_default_channel' which is created in notificationService.ts
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='fcm_default_channel',
                    click_action=click_action, # Only apply if provided
                    icon='notification_icon',
                    color='#F59331',
                    sound='default' # 🔊 Enable sound for Android
                )
            )

            # Prepare iOS config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        category=click_action, # Only apply if provided
                        sound='default' # 🔊 Enable sound for iOS
                    )
                )
            )

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config
            )
            
            # Use to_thread for the synchronous blocking network call
            import asyncio
            response = await asyncio.to_thread(messaging.send, message)
            print(f"✅ Successfully sent notification: {response}")
            return response
        except messaging.UnregisteredError:
            print(f"⚠️ Token is invalid/unregistered. Cleaning up: {token[:20]}...")
            raise ValueError("STALE_TOKEN")
        except Exception as e:
            if "Requested entity was not found" in str(e):
                print(f"⚠️ FCM Token not found in current project. Cleaning up: {token[:20]}...")
                raise ValueError("STALE_TOKEN")
            print(f"❌ Failed to send notification: {e}")
            return None

    async def send_morning_summary(self, token: str, task_count: int, first_task_time: str):
        """Send morning summary notification"""
        title = "Good Morning! ☀️"
        body = f"You have {task_count} tasks today. First task at {first_task_time}."
        data = {"type": "morning_summary"}
        return await self.send_notification(token, title, body, data)

    async def send_evening_summary(self, token: str, completed: int, pending: int):
        """Send evening summary notification"""
        title = "Evening Update 🌙"
        body = f"You completed {completed} tasks today. {pending} still pending."
        data = {"type": "evening_summary"}
        return await self.send_notification(token, title, body, data)

# Singleton instance
fcm_manager = FCMManager()
