from flask import request, jsonify
import random
import json

# โหลดข้อมูลพื้นฐาน (ครู วิชา ห้องเรียน ชั้นเรียน)
with open("timetable.json", "r", encoding="utf-8") as f:
    data = json.load(f)

teachers = data["teachers"]
subjects = data["subjects"]
rooms = data["rooms"]
classes = data["classes"]
days = ["จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์"]
periods = ["08:00-09:00","09:00-10:00","10:00-11:00","11:00-12:00",
           "12:00-13:00","13:00-14:00","14:00-15:00","15:00-16:00","16:00-17:00","17:00-18:00","18:00-19:00"]

def generate_timetable(class_name):
    timetable = []
    used_teacher = {day: [] for day in days}  # ตรวจสอบครูที่ใช้แต่ละวัน
    for day in days:
        for period in periods:
            # ถ้าเป็นช่วงพักเที่ยง
            if period == "12:00-13:00":
                timetable.append({
                    "class": class_name,
                    "day": day,
                    "period": period,
                    "subject": "พักเที่ยง 🍴",
                    "teacher": "",
                    "room": ""
                })
                continue

            subject = random.choice(subjects)
            available_teachers = [t for t in teachers if t not in used_teacher[day]]
            teacher = random.choice(available_teachers) if available_teachers else random.choice(teachers)
            used_teacher[day].append(teacher)
            room = random.choice(rooms)
            timetable.append({
                "class": class_name,
                "day": day,
                "period": period,
                "subject": subject,
                "teacher": teacher,
                "room": room
            })
    return timetable

def register_routes(app):
    @app.route("/generate_timetable", methods=["POST"])
    def generate_timetable_api():
        req = request.json
        class_name = req.get("class")
        if not class_name:
            return jsonify({"error": "โปรดเลือกชั้นเรียน"}), 400
        timetable = generate_timetable(class_name)
        return jsonify(timetable)

    @app.route("/get_classes", methods=["GET"])
    def get_classes():
        return jsonify(classes)
