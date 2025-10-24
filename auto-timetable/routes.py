from flask import request, jsonify
import sqlite3
import random

def register_routes(app):
    @app.route("/")
    def home():
        return "Backend is running!"

    @app.route("/generate_timetable_full", methods=["GET"])
    def generate_timetable_full():
        conn = sqlite3.connect('school.db')
        c = conn.cursor()

        c.execute("SELECT id, name FROM classes")
        classes = c.fetchall()

        c.execute("SELECT id, name, teacher_id FROM subjects")
        subjects = c.fetchall()

        c.execute("SELECT id, name FROM rooms")
        rooms = c.fetchall()

        subject_periods = {1:4, 2:2, 3:3, 4:3}
        c.execute("DELETE FROM timetable")

        days = ["จันทร์","อังคาร","พุธ","พฤหัส","ศุกร์"]
        periods_per_day = 6
        teacher_schedule = {}
        room_schedule = {}

        for cls_id, cls_name in classes:
            for subj_id, subj_name, teacher_id in subjects:
                periods_needed = subject_periods[subj_id]
                assigned_periods = 0
                attempts = 0
                while assigned_periods < periods_needed and attempts < 500:
                    day = random.choice(days)
                    period = random.randint(1, periods_per_day)
                    room_id, room_name = random.choice(rooms)
                    if (teacher_id, day, period) not in teacher_schedule and (room_id, day, period) not in room_schedule:
                        c.execute(
                            "INSERT INTO timetable (class_id, subject_id, room_id, day, period) VALUES (?, ?, ?, ?, ?)",
                            (cls_id, subj_id, room_id, day, period)
                        )
                        teacher_schedule[(teacher_id, day, period)] = True
                        room_schedule[(room_id, day, period)] = True
                        assigned_periods += 1
                    attempts += 1

        conn.commit()
        c.execute('''
            SELECT classes.name, subjects.name, teachers.name, rooms.name, day, period
            FROM timetable
            JOIN classes ON timetable.class_id = classes.id
            JOIN subjects ON timetable.subject_id = subjects.id
            JOIN teachers ON subjects.teacher_id = teachers.id
            JOIN rooms ON timetable.room_id = rooms.id
            ORDER BY classes.name, day, period
        ''')
        rows = c.fetchall()
        conn.close()

        timetable = []
        for r in rows:
            timetable.append({
                "class": r[0],
                "subject": r[1],
                "teacher": r[2],
                "room": r[3],
                "day": r[4],
                "period": r[5]
            })
        return jsonify(timetable)
