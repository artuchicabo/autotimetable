import sqlite3

conn = sqlite3.connect('school.db')
c = conn.cursor()

# ครู
teachers = ["ครูสมชาย", "ครูสมหญิง", "ครูวิทย์", "ครูภาษาอังกฤษ"]
for t in teachers:
    c.execute("INSERT INTO teachers (name) VALUES (?)", (t,))

# ชั้นเรียน
classes = ["ม.1/1", "ม.1/2"]
for cl in classes:
    c.execute("INSERT INTO classes (name) VALUES (?)", (cl,))

# ห้องเรียน
rooms = ["ห้อง A", "ห้อง B"]
for r in rooms:
    c.execute("INSERT INTO rooms (name) VALUES (?)", (r,))

# วิชา (teacher_id)
subjects = [
    ("คณิตศาสตร์", 1),
    ("วิทยาศาสตร์", 3),
    ("ภาษาอังกฤษ", 4),
    ("ประวัติศาสตร์", 2)
]
for s, teacher_id in subjects:
    c.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (s, teacher_id))

conn.commit()
conn.close()
print("Sample data inserted!")
