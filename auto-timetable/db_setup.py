import sqlite3

conn = sqlite3.connect('school.db')
c = conn.cursor()

# ครู
c.execute('''
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

# วิชา
c.execute('''
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
)
''')

# ชั้นเรียน
c.execute('''
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

# ห้องเรียน
c.execute('''
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

# ตารางเรียน
c.execute('''
CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER,
    subject_id INTEGER,
    room_id INTEGER,
    day TEXT,
    period INTEGER,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
)
''')

conn.commit()
conn.close()
print("Database setup completed!")
