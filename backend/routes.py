# อัพเดต 1.0 - routes.py
from flask import jsonify, request, send_file
from firebase_admin import db
from openpyxl import Workbook
from datetime import datetime
import io, random

def register_routes(app):
    base_ref = db.reference('/autotimetable_v1')  # ใช้โหนดเวอร์ชัน 1.0 เพื่อแยกเวอร์ชัน

    # ---------------- Helper ----------------
    def get_map(path):
        """คืนค่า dict ของ id -> data (หรือ {})"""
        ref = base_ref.child(path)
        return ref.get() or {}

    def list_from_map(path):
        m = get_map(path)
        return [{"id": k, **v} for k, v in m.items()]

    def push_data(path, data):
        base_ref.child(path).push(data)

    def set_data_with_id(path, id, data):
        base_ref.child(path).child(id).set(data)

    def delete_data(path, id):
        base_ref.child(path).child(id).delete()

    # ---------------- API: data aggregate ----------------
    @app.route('/api/data', methods=['GET'])
    def api_data():
        return jsonify({
            "teachers": list_from_map('teachers'),
            "subjects": list_from_map('subjects'),
            "rooms": list_from_map('rooms'),
            "times": list_from_map('times'),
            "groups": list_from_map('groups'),
            "timetables": list_from_map('timetables')
        })

    # ---------------- Generic CRUD endpoints ----------------
    @app.route('/api/<entity>', methods=['GET', 'POST', 'DELETE'])
    def api_entity(entity):
        valid = ['teachers', 'subjects', 'rooms', 'times', 'groups']
        if entity not in valid:
            return jsonify({"error": "Invalid entity"}), 400

        if request.method == 'GET':
            return jsonify(list_from_map(entity))

        if request.method == 'POST':
            data = request.get_json() or {}
            # basic validation for subjects/teachers/groups can be done here
            push_data(entity, data)
            return jsonify({"message": "created"})

        if request.method == 'DELETE':
            data = request.get_json() or {}
            id = data.get("id")
            if not id:
                return jsonify({"error": "missing id"}), 400
            delete_data(entity, id)
            return jsonify({"message": "deleted"})

    # ---------------- Add manual timetable entry ----------------
    @app.route('/api/timetable_manual', methods=['POST'])
    def api_timetable_manual():
        """
        รับ JSON:
        {
          "date":"2025-11-05",            # optional ISO date
          "day":"จันทร์",
          "time":"08:00-09:00",
          "period":1,                    # optional
          "subject_code":"101",
          "subject_name":"คณิต",
          "teacher":"ครูสมชาย",
          "room":"101",
          "class":"ปวส.2/1",
          "student_count":30,
          "periods":2
        }
        """
        data = request.get_json() or {}
        # add created_at
        data['created_at'] = datetime.utcnow().isoformat()
        # push to timetables
        push_data('timetables', data)
        return jsonify({"message":"manual entry added"})

    # ---------------- Generate timetable (auto) ----------------
    @app.route('/api/generate_timetable', methods=['POST'])
    def api_generate_timetable():
        teachers = list_from_map('teachers')
        subjects = list_from_map('subjects')
        rooms = list_from_map('rooms')
        times = list_from_map('times')
        groups = list_from_map('groups')

        if not (teachers and subjects and rooms and times and groups):
            return jsonify({"error": "กรุณาเพิ่มข้อมูลพื้นฐานให้ครบ (ครู, วิชา, ห้อง, เวลา, กลุ่ม)"}), 400

        # clear old
        base_ref.child('timetables').delete()

        days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
        created = []
        for day in days:
            for t in times:
                for g in groups:
                    subj = random.choice(subjects)
                    teacher = random.choice(teachers)
                    room = random.choice(rooms)
                    entry = {
                        "date": "",  # leave blank for generated
                        "day": day,
                        "time": t.get("time"),
                        "period": t.get("period", ""),
                        "subject_code": subj.get("code", ""),
                        "subject_name": subj.get("name", ""),
                        "teacher": teacher.get("name", ""),
                        "room": room.get("name", ""),
                        "class": g.get("name", ""),
                        "student_count": int(g.get("size", 0)),
                        "periods": int(subj.get("hours", 1)),
                        "created_at": datetime.utcnow().isoformat()
                    }
                    push_data('timetables', entry)
                    created.append(entry)

        return jsonify({"message":"สร้างตารางเรียบร้อย", "count": len(created)})

    # ---------------- Get timetables ----------------
    @app.route('/api/timetable', methods=['GET'])
    def api_get_timetable():
        items = list_from_map('timetables')
        # sort by day order then time (if provided)
        day_order = {"จันทร์":1,"อังคาร":2,"พุธ":3,"พฤหัสบดี":4,"ศุกร์":5}
        items.sort(key=lambda x: (day_order.get(x.get('day'),99), x.get('time','')))
        return jsonify({"timetable": items})

    # ---------------- Check duplicate (day,time,room) ----------------
    @app.route('/api/check_duplicate', methods=['GET'])
    def api_check_duplicate():
        items = list_from_map('timetables')
        seen = set()
        duplicates = []
        for it in items:
            key = (it.get("day"), it.get("time"), it.get("room"))
            if key in seen:
                duplicates.append(it)
            else:
                seen.add(key)
        return jsonify({"duplicates": duplicates, "status": "ok" if not duplicates else "duplicated"})

    # ---------------- Export Excel (includes all requested fields) ----------------
    @app.route('/api/export_excel', methods=['GET'])
    def api_export_excel():
        try:
            items = list_from_map('timetables')
            wb = Workbook()
            ws = wb.active
            ws.title = "ตารางสอน - อัพเดต 1.0"

            # header as requested
            header = [
                "วันที่ (date)", "วัน", "เวลา", "คาบ (period)", "รหัสวิชา", "รายวิชา",
                "ครูผู้สอน", "ห้องเรียน", "กลุ่ม/ชั้น", "จำนวนนักเรียน", "จำนวนคาบ(สอน)", "created_at"
            ]
            ws.append(header)

            for it in items:
                ws.append([
                    it.get("date",""),
                    it.get("day",""),
                    it.get("time",""),
                    it.get("period",""),
                    it.get("subject_code",""),
                    it.get("subject_name",""),
                    it.get("teacher",""),
                    it.get("room",""),
                    it.get("class",""),
                    it.get("student_count", ""),
                    it.get("periods",""),
                    it.get("created_at","")
                ])

            ws.append([])
            ws.append(["รวมทั้งหมด", "", "", "", "", "", "", "", "", "", "", len(items)])

            stream = io.BytesIO()
            wb.save(stream)
            stream.seek(0)

            return send_file(
                stream,
                as_attachment=True,
                download_name="timetable_update_1.0.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
