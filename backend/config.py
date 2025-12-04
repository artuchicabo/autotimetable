import os
import csv
import firebase_admin
from firebase_admin import credentials, db

# ---------------------------------------
# 1) Firebase Initialization
# ---------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

cred = credentials.Certificate(os.path.join(BASE_DIR, "./key2.json"))
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://autotimetable-382ee-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

print("[OK] Firebase connected!")


# ---------------------------------------
# 2) CSV Upload Function
# ---------------------------------------
def upload_csv(file_name, table_name, key_column=None):
    """
    file_name: ชื่อไฟล์ CSV
    table_name: path ของ Firebase
    key_column: ถ้ามี → ใช้เป็น key ของ object
    """
    path = os.path.join(BASE_DIR, file_name)

    if not os.path.exists(path):
        print(f"[SKIP] Not found: {file_name}")
        return

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    ref = db.reference(table_name)

    if key_column:
        # Upload as dictionary keyed by ID
        data = {row[key_column]: row for row in rows}
        ref.set(data)
    else:
        # Upload as list
        ref.set(rows)

    print(f"[OK] Uploaded {len(rows)} records → /{table_name}")


# ---------------------------------------
# 3) Upload ALL CSV FILES
# ---------------------------------------

# 1. teacher.csv
upload_csv("teacher.csv", "teachers", "teacher_id")

# 2. subject.csv
upload_csv("subject.csv", "subjects", "subject_id")

# 3. student_group.csv
upload_csv("student_group.csv", "student_groups", "group_id")

# 4. room.csv
upload_csv("room.csv", "rooms", "room_id")

# 5. timeslot.csv
upload_csv("timeslot.csv", "timeslots", "timeslot_id")

# 6. register.csv
upload_csv("register.csv", "register")

# 7. teach.csv
upload_csv("teach.csv", "teach")

# 8. timetableoutput.csv
upload_csv("timetableoutput.csv", "timetable_output")

print("\n🎉 All CSV imported successfully!")
