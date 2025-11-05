import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("config/Key.json")
firebase_admin.initialize_app(cred)
