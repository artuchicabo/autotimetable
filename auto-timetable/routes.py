from flask import Blueprint, jsonify, request
from data_store import teachers, subjects, rooms, classes, days, periods


DATA_FILE = "timetable.json"


# โหลดข้อมูลจากไฟล์
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"departments": [], "majors": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# บันทึกข้อมูลกลับไฟล์
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ฟังก์ชันหลัก ที่ app.py จะเรียกใช้
def register_routes(app):

    #  1. แผนก (Departments)

    @app.route("/api/departments", methods=["GET"])
    def get_departments():
        data = load_data()
        return jsonify(data["departments"])

    @app.route("/api/departments", methods=["POST"])
    def add_department():
        data = load_data()
        new_dept = request.get_json()
        if not new_dept.get("dept_id") or not new_dept.get("dept_name"):
            return jsonify({"error": "ต้องระบุ dept_id และ dept_name"}), 400
        data["departments"].append(new_dept)
        save_data(data)
        return jsonify({"message": "เพิ่มแผนกเรียบร้อย", "data": new_dept}), 201

    @app.route("/api/departments/<dept_id>", methods=["PUT"])
    def update_department(dept_id):
        data = load_data()
        for dept in data["departments"]:
            if dept["dept_id"] == dept_id:
                dept.update(request.get_json())
                save_data(data)
                return jsonify({"message": "แก้ไขข้อมูลแผนกเรียบร้อย", "data": dept})
        return jsonify({"error": "ไม่พบแผนกที่ระบุ"}), 404

    @app.route("/api/departments/<dept_id>", methods=["DELETE"])
    def delete_department(dept_id):
        data = load_data()
        new_list = [d for d in data["departments"] if d["dept_id"] != dept_id]
        if len(new_list) == len(data["departments"]):
            return jsonify({"error": "ไม่พบแผนกที่ต้องการลบ"}), 404
        data["departments"] = new_list
        save_data(data)
        return jsonify({"message": f"ลบแผนก {dept_id} เรียบร้อย"})

    #  2. สาขาวิชา (Majors)

    @app.route("/api/majors", methods=["GET"])
    def get_majors():
        data = load_data()
        return jsonify(data["majors"])

    @app.route("/api/majors", methods=["POST"])
    def add_major():
        data = load_data()
        new_major = request.get_json()
        if not all(k in new_major for k in ["major_id", "major_name", "dept_id"]):
            return jsonify({"error": "ต้องระบุ major_id, major_name และ dept_id"}), 400
        data["majors"].append(new_major)
        save_data(data)
        return jsonify({"message": "เพิ่มสาขาวิชาเรียบร้อย", "data": new_major}), 201

    @app.route("/api/majors/<major_id>", methods=["PUT"])
    def update_major(major_id):
        data = load_data()
        for m in data["majors"]:
            if m["major_id"] == major_id:
                m.update(request.get_json())
                save_data(data)
                return jsonify({"message": "แก้ไขข้อมูลสาขาวิชาเรียบร้อย", "data": m})
        return jsonify({"error": "ไม่พบสาขาที่ระบุ"}), 404

    @app.route("/api/majors/<major_id>", methods=["DELETE"])
    def delete_major(major_id):
        data = load_data()
        new_list = [m for m in data["majors"] if m["major_id"] != major_id]
        if len(new_list) == len(data["majors"]):
            return jsonify({"error": "ไม่พบสาขาวิชาที่ต้องการลบ"}), 404
        data["majors"] = new_list
        save_data(data)
        return jsonify({"message": f"ลบสาขาวิชา {major_id} เรียบร้อย"})


