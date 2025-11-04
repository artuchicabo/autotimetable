import json

with open("timetable.json", "r", encoding="utf-8") as f:
    data = json.load(f)

major = data.get("majors", [])
major_name = data.get("major_name", [])
major_id = data.get("major_id", [])

dept = data.get("departments", [])
dept_name = data.get("dept_name", [])
dept_id = data.get("dept_id", [])
