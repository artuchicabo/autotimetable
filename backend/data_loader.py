import csv
import os

from models.subject import Subject
from models.teacher import Teacher
from models.student_group import StudentGroup
from models.room import Room
from models.timeslot import Timeslot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

def _path(name: str) -> str:
    return os.path.join(DATASET_DIR, name)

def load_subjects(path=_path("subject.csv")):
    subjects = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj = Subject(**row)
            subjects[subj.subject_id] = subj
    return subjects

def load_teachers(path=_path("teacher.csv")):
    teachers = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = Teacher(**row)
            teachers[t.teacher_id] = t
    return teachers

def load_rooms(path=_path("room.csv")):
    rooms = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = Room(**row)
            rooms[r.room_id] = r
    return rooms

def load_groups(path=_path("student_group.csv")):
    groups = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g = StudentGroup(**row)
            groups[g.group_id] = g
    return groups

def load_timeslots(path=_path("timeslot.csv")):
    timeslots = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = Timeslot(**row)
            timeslots[ts.timeslot_id] = ts
    return timeslots
