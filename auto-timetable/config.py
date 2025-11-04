import firebase_admin

from firebase_admin import credentials, db

cred = credentials.Certificate("config/serviceAccountkey.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://autotimetable-382ee-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

ref = db.reference('teachers')
ref.push({
    'name': 'Test Teacher',
    'subject': 'Mathematics',
    "available": ["Monday 9am-10am", "Wednesday 1pm-2pm"]
})

all_teachers = ref.get()
print("All Teachers:", all_teachers)