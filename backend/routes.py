from flask import jsonify, request, send_file
from firebase_admin import db
from openpyxl import Workbook
from datetime import datetime
import io, random


def register_routes(app):
    # ✅ root path ของฐานข้อมูล
    base_ref = db.reference('/autotimetable')

    # ---------------- Helper ----------------
    def get_list(path):
        """อ่านข้อมูลจาก path ใน Realtime DB"""
        ref = base_ref.child(path)
        data = ref.get() or {}
        return [{"id": k, **v} for k, v in data.items()]

    def push_data(path, data):
        """เพิ่มข้อมูลใหม่"""
        base_ref.child(path).push(data)

    def delete_data(path, id):
        """ลบข้อมูลตาม id"""
        base_ref.child(path).child(id).delete()

    # ---------------- ดึงข้อมูลรวมทั้งหมด (Dashboard ใช้) ----------------
    @app.route('/api/data', methods=['GET'])
    def api_get_data():
        return jsonify({
            "teachers": get_list('teachers'),
            "subjects": get_list('subjects'),
            "rooms": get_list('rooms'),
            "times": get_list('times'),
            "groups": get_list('groups')
        })

    # ---------------- CRUD (ครู, วิชา, ห้อง, เวลา, กลุ่ม) ----------------
    @app.route('/api/<entity>', methods=['GET', 'POST', 'DELETE'])
    def api_entity(entity):
        valid = ['teachers', 'subjects', 'rooms', 'times', 'groups']
        if entity not in valid:
            return jsonify({"error": "Invalid entity"}), 400

        # ดึงทั้งหมด
        if request.method == 'GET':
            return jsonify(get_list(entity))

        # เพิ่มข้อมูลใหม่
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "missing data"}), 400
            push_data(entity, data)
            return jsonify({"message": "created"})

        # ลบข้อมูล
        if request.method == 'DELETE':
            data = request.get_json()
            id = data.get("id")
            if not id:
                return jsonify({"error": "missing id"}), 400
            delete_data(entity, id)
            return jsonify({"message": "deleted"})

    # ---------------- สร้างตารางสอนอัตโนมัติ ----------------
    @app.route('/api/generate_timetable', methods=['POST'])
    def api_generate_timetable():
        try:
            teachers = get_list('teachers')
            subjects = get_list('subjects')
            rooms = get_list('rooms')
            times = get_list('times')
            groups = get_list('groups')

            # ตรวจสอบว่ามีข้อมูลพื้นฐานครบหรือยัง
            if not (teachers and subjects and rooms and times and groups):
                return jsonify({"error": "กรุณาเพิ่มข้อมูลพื้นฐานให้ครบ"}), 400

            # ล้างข้อมูลเก่าก่อนสร้างใหม่
            timetable_ref = base_ref.child('timetables')
            timetable_ref.delete()

            days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
            timetable = []

            for day in days:
                for t in times:
                    for g in groups:
                        subj = random.choice(subjects)
                        teacher = random.choice(teachers)
                        room = random.choice(rooms)
                        item = {
                            "day": day,
                            "time": t.get("time"),
                            "subject_code": subj.get("code", ""),
                            "subject_name": subj.get("name", ""),
                            "teacher": teacher.get("name", ""),
                            "room": room.get("name", ""),
                            "class": g.get("name", ""),
                            "slots": subj.get("hours", 1),
                            "created_at": datetime.utcnow().isoformat()
                        }
                        timetable_ref.push(item)
                        timetable.append(item)

            return jsonify({"message": "สร้างตารางเรียบร้อย", "count": len(timetable)})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---------------- ดึงตารางสอนทั้งหมด ----------------
    @app.route('/api/timetable', methods=['GET'])
    def api_get_timetable():
        data = get_list('timetables')
        # เรียงตามวันและเวลา
        day_order = {"จันทร์": 1, "อังคาร": 2, "พุธ": 3, "พฤหัสบดี": 4, "ศุกร์": 5}
        data.sort(key=lambda x: (day_order.get(x.get("day"), 99), x.get("time", "")))
        return jsonify({"timetable": data})

    # ---------------- ตรวจสอบข้อมูลซ้ำ (วัน+เวลา+ห้อง) ----------------
    @app.route('/api/check_duplicate', methods=['GET'])
    def api_check_duplicate():
        items = get_list('timetables')
        seen = set()
        duplicates = []
        for it in items:
            key = (it.get("day"), it.get("time"), it.get("room"))
            if key in seen:
                duplicates.append(it)
            else:
                seen.add(key)
        return jsonify({
            "duplicates": duplicates,
            "status": "ok" if not duplicates else "duplicated"
        })

    # ---------------- Export Excel ----------------
    @app.route('/api/export_excel', methods=['GET'])
    def api_export_excel():
        try:
            items = get_list('timetables')

            wb = Workbook()
            ws = wb.active
            ws.title = "ตารางสอน"

            ws.append(["วัน", "เวลา", "รหัสวิชา", "รายวิชา", "ครูผู้สอน", "ห้องเรียน", "กลุ่ม", "คาบ"])
            for i in items:
                ws.append([
                    i.get("day", ""),
                    i.get("time", ""),
                    i.get("subject_code", ""),
                    i.get("subject_name", ""),
                    i.get("teacher", ""),
                    i.get("room", ""),
                    i.get("class", ""),
                    i.get("slots", 1)
                ])

            ws.append([])
            ws.append(["รวมทั้งหมด", "", "", "", "", "", "", len(items)])

            stream = io.BytesIO()
            wb.save(stream)
            stream.seek(0)

            return send_file(
                stream,
                as_attachment=True,
                download_name="timetable.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
