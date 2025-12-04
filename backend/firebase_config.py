import firebase_admin
from firebase_admin import credentials, db
import os

# Path to service account key - using key2.json which is used by config.py
SERVICE_ACCOUNT_KEY_PATH = os.path.join(os.path.dirname(__file__), "key2.json")

# Firebase Realtime Database URL
DATABASE_URL = "https://autotimetable-382ee-default-rtdb.asia-southeast1.firebasedatabase.app/"

rtdb = None  # Realtime Database reference

def initialize_firebase():
    global rtdb
    if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        print(f"WARNING: Firebase service account key not found at {SERVICE_ACCOUNT_KEY_PATH}. Real-time sync will be disabled.")
        return None

    try:
        # Check if already initialized
        try:
            firebase_admin.get_app()
            print("Firebase already initialized, reusing existing app.")
        except ValueError:
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred, {
                "databaseURL": DATABASE_URL
            })
            print("Firebase initialized successfully.")
        
        rtdb = db  # Get reference to Realtime Database module
        return rtdb
    except Exception as e:
        print(f"ERROR: Failed to initialize Firebase: {e}")
        return None

# Initialize on module load
initialize_firebase()
