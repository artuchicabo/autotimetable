from flask import Blueprint, jsonify, request
import pandas as pd
import os
import threading
import csv

from data_loader import (
    load_subjects,
    load_teachers,
    load_rooms,
    load_groups,
    load_timeslots
)
from auth import login_user, require_auth
from firebase_config import rtdb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
TIMETABLE_FILE = os.path.join(BASE_DIR, "timetable.csv")

api_blueprint = Blueprint("api", __name__)

# Helper to reload data
def reload_data():
    global subjects, teachers, rooms, groups, timeslots
    subjects = load_subjects()
    teachers = load_teachers()
    rooms = load_rooms()
    groups = load_groups()
    timeslots = load_timeslots()

# Load data at startup
subjects = load_subjects()
teachers = load_teachers()
rooms = load_rooms()
groups = load_groups()
timeslots = load_timeslots()

# ---------- AUTH ----------

@api_blueprint.post("/login")
def login():
    data = request.json or {}
    teacher_id = data.get("teacher_id")
    password = data.get("password")

    token, status = login_user(teacher_id, password)

    if status != "SUCCESS":
        return jsonify({"status": status}), 401

    user = teachers.get(teacher_id)
    user_info = user.to_dict() if user else {}
    
    return jsonify({
        "status": "OK", 
        "token": token,
        "user": user_info
    })

@api_blueprint.get("/me")
@require_auth()
def me():
    return jsonify(request.user)

# ---------- BASIC DATA ----------

@api_blueprint.get("/teachers")
@require_auth()
def get_teachers():
    reload_data()
    return jsonify([t.to_dict() for t in teachers.values()])

@api_blueprint.get("/subjects")
@require_auth()
def get_subjects():
    reload_data()
    return jsonify([s.to_dict() for s in subjects.values()])

@api_blueprint.get("/rooms")
@require_auth()
def get_rooms():
    reload_data()
    return jsonify([r.to_dict() for r in rooms.values()])

@api_blueprint.get("/groups")
@require_auth()
def get_groups():
    reload_data()
    return jsonify([g.to_dict() for g in groups.values()])

@api_blueprint.get("/timeslots")
@require_auth()
def get_timeslots():
    reload_data()
    return jsonify([t.to_dict() for t in timeslots.values()])

# ---------- STATS ----------

@api_blueprint.get("/stats")
@require_auth()
def get_stats():
    reload_data()
    timetable_count = 0
    if os.path.exists(TIMETABLE_FILE):
        df = pd.read_csv(TIMETABLE_FILE)
        timetable_count = len(df)
    
    # Load register and teach counts
    register_count = 0
    teach_count = 0
    try:
        register_df = pd.read_csv(os.path.join(DATASET_DIR, "register.csv"))
        register_count = len(register_df.dropna(how='all'))
    except:
        pass
    try:
        teach_df = pd.read_csv(os.path.join(DATASET_DIR, "teach.csv"))
        teach_count = len(teach_df.dropna(how='all'))
    except:
        pass
    
    return jsonify({
        "teachers": len(teachers),
        "subjects": len(subjects),
        "rooms": len(rooms),
        "groups": len(groups),
        "timeslots": len(timeslots),
        "timetable_entries": timetable_count,
        "register_count": register_count,
        "teach_count": teach_count
    })

# ---------- TIMETABLE VIEW ----------

def _load_timetable_df():
    if not os.path.exists(TIMETABLE_FILE):
        return pd.DataFrame()
    df = pd.read_csv(TIMETABLE_FILE)
    return df

def _enrich_timetable(df):
    if df.empty:
        return df
    
    reload_data()
    
    # Add timeslot details
    timeslot_data = {int(ts.timeslot_id): ts.to_dict() for ts in timeslots.values()}
    
    def get_timeslot_attr(tid, attr):
        ts = timeslot_data.get(int(tid) if pd.notna(tid) else None, {})
        return ts.get(attr, "")
    
    df["day"] = df["timeslot_id"].apply(lambda x: get_timeslot_attr(x, "day"))
    df["period"] = df["timeslot_id"].apply(lambda x: get_timeslot_attr(x, "period"))
    df["start"] = df["timeslot_id"].apply(lambda x: get_timeslot_attr(x, "start"))
    df["end"] = df["timeslot_id"].apply(lambda x: get_timeslot_attr(x, "end"))
    
    # Add subject name
    subject_data = {s.subject_id: s.to_dict() for s in subjects.values()}
    df["subject_name"] = df["subject_id"].apply(lambda x: subject_data.get(x, {}).get("subject_name", ""))
    
    # Add teacher name
    teacher_data = {t.teacher_id: t.to_dict() for t in teachers.values()}
    df["teacher_name"] = df["teacher_id"].apply(lambda x: teacher_data.get(x, {}).get("teacher_name", ""))
    
    # Add room name  
    room_data = {r.room_id: r.to_dict() for r in rooms.values()}
    df["room_name"] = df["room_id"].apply(lambda x: room_data.get(x, {}).get("room_name", ""))
    
    # Add group name
    group_data = {g.group_id: g.to_dict() for g in groups.values()}
    df["group_name"] = df["group_id"].apply(lambda x: group_data.get(x, {}).get("group_name", ""))
    
    return df

@api_blueprint.get("/timetable")
@require_auth()
def get_full_timetable():
    df = _load_timetable_df()
    df = _enrich_timetable(df)
    return jsonify(df.to_dict(orient="records"))

@api_blueprint.get("/timetable/group/<group_id>")
@require_auth()
def get_group_timetable(group_id):
    df = _load_timetable_df()
    if df.empty:
        return jsonify([])
    result = df[df["group_id"] == group_id]
    result = _enrich_timetable(result)
    result = result.sort_values(["day", "period"])
    return jsonify(result.to_dict(orient="records"))

@api_blueprint.get("/timetable/teacher/<teacher_id>")
@require_auth()
def get_teacher_timetable(teacher_id):
    df = _load_timetable_df()
    if df.empty:
        return jsonify([])
    result = df[df["teacher_id"] == teacher_id]
    result = _enrich_timetable(result)
    result = result.sort_values(["day", "period"])
    return jsonify(result.to_dict(orient="records"))

@api_blueprint.get("/timetable/room/<room_id>")
@require_auth()
def get_room_timetable(room_id):
    df = _load_timetable_df()
    if df.empty:
        return jsonify([])
    result = df[df["room_id"] == room_id]
    result = _enrich_timetable(result)
    result = result.sort_values(["day", "period"])
    return jsonify(result.to_dict(orient="records"))

# ---------- RUN GA SCHEDULING ----------

@api_blueprint.post("/schedule/run")
@require_auth("admin")
def run_scheduler():
    from MachineLearning import run_scheduling, get_status
    
    status = get_status()
    if status.get('running'):
        return jsonify({
            "status": "ALREADY_RUNNING",
            "message": "Scheduling is already in progress"
        }), 409
    
    def run_in_background():
        run_scheduling()
    
    thread = threading.Thread(target=run_in_background)
    thread.start()
    
    return jsonify({
        "status": "STARTED",
        "message": "Scheduling started in background"
    })

@api_blueprint.get("/schedule/status")
@require_auth()
def get_schedule_status():
    from MachineLearning import get_status
    return jsonify(get_status())

@api_blueprint.post("/schedule/run-sync")
@require_auth("admin")
def run_scheduler_sync():
    from MachineLearning import run_scheduling
    result = run_scheduling()
    return jsonify(result)

# ---------- EXPORT ----------

@api_blueprint.get("/export/excel")
def export_excel():
    # No auth for simplicity in download, or use query param token if needed.
    # For now, let's assume it's open or browser handles cookies if we had them.
    # But we use JWT header, so browser download is tricky. 
    # We'll allow it without auth for now or expect a token in query param?
    # Let's keep it simple: No auth for this demo or use token in URL.
    
    df = _load_timetable_df()
    if df.empty:
        return jsonify({"error": "No timetable data"}), 404
        
    df = _enrich_timetable(df)
    
    # Format for export
    export_df = df[[
        "day", "period", "start", "end", 
        "subject_id", "subject_name", 
        "teacher_name", "room_name", "group_name"
    ]].sort_values(["day", "period", "group_name"])
    
    # Create Excel
    from io import BytesIO
    output = BytesIO()
    
    # Requires openpyxl
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Timetable')
    except ImportError:
        return jsonify({"error": "openpyxl not installed"}), 500
        
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output, 
        download_name="timetable.xlsx", 
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ============================================================
# CRUD ENDPOINTS FOR DATA MANAGEMENT
# ============================================================

def save_csv(filename, data, fieldnames):
    """Save data to CSV file"""
    filepath = os.path.join(DATASET_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# ---------- TEACHERS CRUD ----------

@api_blueprint.post("/teachers")
@require_auth("admin")
def add_teacher():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "teacher.csv")
    
    # Read existing
    df = pd.read_csv(filepath)
    
    # Check duplicate
    if data.get("teacher_id") in df["teacher_id"].values:
        return jsonify({"error": "Teacher ID already exists"}), 400
    
    # Add new row
    new_row = pd.DataFrame([{
        "teacher_id": data.get("teacher_id"),
        "teacher_name": data.get("teacher_name"),
        "password": data.get("password", "12345"),
        "role": data.get("role", "teacher")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            teacher_data = {
                "teacher_id": data.get("teacher_id"),
                "teacher_name": data.get("teacher_name"),
                "role": data.get("role", "teacher")
            }
            rtdb.reference("teachers/" + str(data.get("teacher_id"))).set(teacher_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK", "message": "Teacher added"})

@api_blueprint.put("/teachers/<teacher_id>")
@require_auth("admin")
def update_teacher(teacher_id):
    data = request.json
    filepath = os.path.join(DATASET_DIR, "teacher.csv")
    df = pd.read_csv(filepath)
    
    idx = df[df["teacher_id"] == teacher_id].index
    if idx.empty:
        return jsonify({"error": "Teacher not found"}), 404
    
    for key in ["teacher_name", "password", "role"]:
        if key in data:
            df.loc[idx, key] = data[key]
    
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            updated_data = {
                "teacher_id": teacher_id,
                "teacher_name": df.loc[idx, "teacher_name"].values[0],
                "role": df.loc[idx, "role"].values[0]
            }
            rtdb.reference("teachers/" + str(teacher_id)).update(updated_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.delete("/teachers/<teacher_id>")
@require_auth("admin")
def delete_teacher(teacher_id):
    filepath = os.path.join(DATASET_DIR, "teacher.csv")
    df = pd.read_csv(filepath)
    df = df[df["teacher_id"] != teacher_id]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            rtdb.reference("teachers/" + str(teacher_id)).delete()
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

# ---------- SUBJECTS CRUD ----------

@api_blueprint.post("/subjects")
@require_auth("admin")
def add_subject():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "subject.csv")
    df = pd.read_csv(filepath)
    
    if data.get("subject_id") in df["subject_id"].values:
        return jsonify({"error": "Subject ID already exists"}), 400
    
    new_row = pd.DataFrame([{
        "subject_id": data.get("subject_id"),
        "subject_name": data.get("subject_name"),
        "theory": int(data.get("theory", 0)),
        "practice": int(data.get("practice", 0)),
        "credit": int(data.get("credit", 0))
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            subject_data = {
                "subject_id": data.get("subject_id"),
                "subject_name": data.get("subject_name"),
                "theory": int(data.get("theory", 0)),
                "practice": int(data.get("practice", 0)),
                "credit": int(data.get("credit", 0))
            }
            rtdb.reference("subjects/" + str(data.get("subject_id"))).set(subject_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.put("/subjects/<subject_id>")
@require_auth("admin")
def update_subject(subject_id):
    data = request.json
    filepath = os.path.join(DATASET_DIR, "subject.csv")
    df = pd.read_csv(filepath)
    
    idx = df[df["subject_id"] == subject_id].index
    if idx.empty:
        return jsonify({"error": "Subject not found"}), 404
    
    for key in ["subject_name", "theory", "practice", "credit"]:
        if key in data:
            df.loc[idx, key] = data[key]
    
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            updated_data = {
                "subject_id": subject_id,
                "subject_name": df.loc[idx, "subject_name"].values[0],
                "theory": int(df.loc[idx, "theory"].values[0]),
                "practice": int(df.loc[idx, "practice"].values[0]),
                "credit": int(df.loc[idx, "credit"].values[0])
            }
            rtdb.reference("subjects/" + str(subject_id)).update(updated_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.delete("/subjects/<subject_id>")
@require_auth("admin")
def delete_subject(subject_id):
    filepath = os.path.join(DATASET_DIR, "subject.csv")
    df = pd.read_csv(filepath)
    df = df[df["subject_id"] != subject_id]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            rtdb.reference("subjects/" + str(subject_id)).delete()
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

# ---------- ROOMS CRUD ----------

@api_blueprint.post("/rooms")
@require_auth("admin")
def add_room():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "room.csv")
    df = pd.read_csv(filepath)
    
    if data.get("room_id") in df["room_id"].values:
        return jsonify({"error": "Room ID already exists"}), 400
    
    new_row = pd.DataFrame([{
        "room_id": data.get("room_id"),
        "room_name": data.get("room_name")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            room_data = {
                "room_id": data.get("room_id"),
                "room_name": data.get("room_name")
            }
            rtdb.reference("rooms/" + str(data.get("room_id"))).set(room_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.delete("/rooms/<room_id>")
@require_auth("admin")
def delete_room(room_id):
    filepath = os.path.join(DATASET_DIR, "room.csv")
    df = pd.read_csv(filepath)
    df = df[df["room_id"] != room_id]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            rtdb.reference("rooms/" + str(room_id)).delete()
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.put("/rooms/<room_id>")
@require_auth("admin")
def update_room(room_id):
    data = request.json
    filepath = os.path.join(DATASET_DIR, "room.csv")
    df = pd.read_csv(filepath)
    
    idx = df[df["room_id"] == room_id].index
    if idx.empty:
        return jsonify({"error": "Room not found"}), 404
    
    if "room_name" in data:
        df.loc[idx, "room_name"] = data["room_name"]
    
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            updated_data = {
                "room_id": room_id,
                "room_name": df.loc[idx, "room_name"].values[0]
            }
            rtdb.reference("rooms/" + str(room_id)).update(updated_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

# ---------- STUDENT GROUPS CRUD ----------

@api_blueprint.post("/groups")
@require_auth("admin")
def add_group():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "student_group.csv")
    df = pd.read_csv(filepath)
    
    if data.get("group_id") in df["group_id"].values:
        return jsonify({"error": "Group ID already exists"}), 400
    
    new_row = pd.DataFrame([{
        "group_id": data.get("group_id"),
        "group_name": data.get("group_name"),
        "student_count": int(data.get("student_count", 0)),
        "advisor": data.get("advisor", "")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            group_data = {
                "group_id": data.get("group_id"),
                "group_name": data.get("group_name"),
                "student_count": int(data.get("student_count", 0)),
                "advisor": data.get("advisor", "")
            }
            rtdb.reference("groups/" + str(data.get("group_id"))).set(group_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.delete("/groups/<group_id>")
@require_auth("admin")
def delete_group(group_id):
    filepath = os.path.join(DATASET_DIR, "student_group.csv")
    df = pd.read_csv(filepath)
    df = df[df["group_id"] != group_id]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            rtdb.reference("groups/" + str(group_id)).delete()
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.put("/groups/<group_id>")
@require_auth("admin")
def update_group(group_id):
    data = request.json
    filepath = os.path.join(DATASET_DIR, "student_group.csv")
    df = pd.read_csv(filepath)
    
    idx = df[df["group_id"] == group_id].index
    if idx.empty:
        return jsonify({"error": "Group not found"}), 404
    
    for key in ["group_name", "student_count", "advisor"]:
        if key in data:
            df.loc[idx, key] = data[key]
    
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    reload_data()

    # Sync to Firebase
    if rtdb:
        try:
            updated_data = {
                "group_id": group_id,
                "group_name": df.loc[idx, "group_name"].values[0],
                "student_count": int(df.loc[idx, "student_count"].values[0]),
                "advisor": df.loc[idx, "advisor"].values[0] if "advisor" in df.columns else ""
            }
            rtdb.reference("groups/" + str(group_id)).update(updated_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

# ---------- REGISTER (Group-Subject) CRUD ----------

@api_blueprint.get("/register")
@require_auth()
def get_register():
    filepath = os.path.join(DATASET_DIR, "register.csv")
    df = pd.read_csv(filepath).dropna(how='all')
    return jsonify(df.to_dict(orient="records"))

@api_blueprint.post("/register")
@require_auth("admin")
def add_register():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "register.csv")
    df = pd.read_csv(filepath)
    
    # Check duplicate
    exists = df[(df["group_id"] == data.get("group_id")) & 
                (df["subject_id"] == data.get("subject_id"))]
    if not exists.empty:
        return jsonify({"error": "Registration already exists"}), 400
    
    new_row = pd.DataFrame([{
        "group_id": data.get("group_id"),
        "subject_id": data.get("subject_id")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    # Sync to Firebase
    if rtdb:
        try:
            reg_id = f"{data.get('group_id')}_{data.get('subject_id')}"
            reg_data = {
                "group_id": data.get("group_id"),
                "subject_id": data.get("subject_id")
            }
            rtdb.reference("register/" + str(reg_id)).set(reg_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.delete("/register")
@require_auth("admin")
def delete_register():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "register.csv")
    df = pd.read_csv(filepath)
    
    mask = (df["group_id"] == data.get("group_id")) & (df["subject_id"] == data.get("subject_id"))
    df = df[~mask]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    # Sync to Firebase
    if rtdb:
        try:
            reg_id = f"{data.get('group_id')}_{data.get('subject_id')}"
            rtdb.reference("register/" + str(reg_id)).delete()
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

# ---------- TEACH (Teacher-Subject) CRUD ----------

@api_blueprint.get("/teach")
@require_auth()
def get_teach():
    filepath = os.path.join(DATASET_DIR, "teach.csv")
    df = pd.read_csv(filepath).dropna(how='all')
    return jsonify(df.to_dict(orient="records"))

@api_blueprint.post("/teach")
@require_auth("admin")
def add_teach():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "teach.csv")
    df = pd.read_csv(filepath)
    
    exists = df[(df["teacher_id"] == data.get("teacher_id")) & 
                (df["subject_id"] == data.get("subject_id"))]
    if not exists.empty:
        return jsonify({"error": "Teaching assignment already exists"}), 400
    
    new_row = pd.DataFrame([{
        "teacher_id": data.get("teacher_id"),
        "subject_id": data.get("subject_id")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    # Sync to Firebase
    if rtdb:
        try:
            teach_id = f"{data.get('teacher_id')}_{data.get('subject_id')}"
            teach_data = {
                "teacher_id": data.get("teacher_id"),
                "subject_id": data.get("subject_id")
            }
            rtdb.reference("teach/" + str(teach_id)).set(teach_data)
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})

@api_blueprint.delete("/teach")
@require_auth("admin")
def delete_teach():
    data = request.json
    filepath = os.path.join(DATASET_DIR, "teach.csv")
    df = pd.read_csv(filepath)
    
    mask = (df["teacher_id"] == data.get("teacher_id")) & (df["subject_id"] == data.get("subject_id"))
    df = df[~mask]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    # Sync to Firebase
    if rtdb:
        try:
            teach_id = f"{data.get('teacher_id')}_{data.get('subject_id')}"
            rtdb.reference("teach/" + str(teach_id)).delete()
        except Exception as e:
            print(f"Firebase sync error: {e}")

    return jsonify({"status": "OK"})
