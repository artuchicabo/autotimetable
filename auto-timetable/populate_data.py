import sqlite3

conn = sqlite3.connect('school.db')
c = conn.cursor()

# ครู
teachers = ["นาย พิชญะ พรมลา", "นาย กรรัก พร้อมจะบก", "นางสาวสุวนันท์ กอศรีรมย์", "นาย ประจิตร์ เลขตะระโก","นาวบังอร เลขะตะระโก","นาย นิราชัน กุลชัย"]
for t in teachers:
    c.execute("INSERT INTO teachers (name) VALUES (?)", (t,))

# ชั้นเรียน
classes = ["ปวส.2/1", "ปวส.2/2"]
for cl in classes:
    c.execute("INSERT INTO classes (name) VALUES (?)", (cl,))

# ห้องเรียน
rooms = ["LAB 6405", "LAB 6406", "LAB 6407", "LAB 6408"]
for r in rooms:
    c.execute("INSERT INTO rooms (name) VALUES (?)", (r,))

# วิชา (teacher_id)
subjects = [
    ("โครงสร้างและอัลกอริทึม", 1),
    ("การพัฒซอฟต์แวร์เชิงวัตถุ", 3),
    ("การออกแบบฐานข้อมูล", 4),
    ("การเป็นผู้ประกอบการ", 2)
]
for s, teacher_id in subjects:
    c.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (s, teacher_id))

conn.commit()
conn.close()
print("Sample data inserted!")
