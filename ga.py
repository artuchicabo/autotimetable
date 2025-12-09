import pandas as pd
import random
import itertools

print("🚀 เริ่มระบบ AI Scheduling (Genetic Algorithm)...")

# -------------------------------
# โหลดข้อมูล CSV
# -------------------------------
DATASET_PATH = "dataset/"

groups = pd.read_csv(DATASET_PATH + "student_group.csv")
subjects = pd.read_csv(DATASET_PATH + "subject.csv")
teachers = pd.read_csv(DATASET_PATH + "teacher.csv")
rooms = pd.read_csv(DATASET_PATH + "room.csv")
timeslots = pd.read_csv(DATASET_PATH + "timeslot.csv")
teach = pd.read_csv(DATASET_PATH + "teach.csv")
register = pd.read_csv(DATASET_PATH + "register.csv")

# -------------------------------
# กำหนดโครงสร้างข้อมูลตารางสอน
# -------------------------------
def create_gene():
    """สร้าง gene หนึ่งชุด = หนึ่งคาบเรียน"""
    row = register.sample(1).iloc[0]
    group_id = row["group_id"]
    subject_id = row["subject_id"]

    # หาครูที่สอนวิชานี้ได้
    teachable = teach[teach["subject_id"] == subject_id]
    if teachable.empty:
        teacher_id = random.choice(teachers["teacher_id"].tolist())
    else:
        teacher_id = random.choice(teachable["teacher_id"].tolist())

    room_id = random.choice(rooms["room_id"].tolist())
    timeslot = timeslots.sample(1).iloc[0]
    day, period = timeslot["day"], timeslot["period"]

    return {
        "group_id": group_id,
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "room_id": room_id,
        "day": day,
        "period": period
    }

# -------------------------------
# สร้างประชากรเริ่มต้น
# -------------------------------
def create_population(size):
    return [[create_gene() for _ in range(len(register))] for _ in range(size)]

# -------------------------------
# ฟังก์ชันคำนวณความเหมาะสม (Fitness)
# -------------------------------
def fitness(schedule):
    score = 1000  # เริ่มต้น 1000 คะแนน

    # ตรวจชนกัน: ครู / ห้อง / กลุ่มเรียน ในเวลาเดียวกัน
    for a, b in itertools.combinations(schedule, 2):
        if a["day"] == b["day"] and a["period"] == b["period"]:
            if a["teacher_id"] == b["teacher_id"]:
                score -= 10
            if a["room_id"] == b["room_id"]:
                score -= 10
            if a["group_id"] == b["group_id"]:
                score -= 10
    return max(score, 0)

# -------------------------------
# การเลือก (Selection)
# -------------------------------
def selection(population):
    population = sorted(population, key=fitness, reverse=True)
    return population[:2]

# -------------------------------
# การผสมพันธุ์ (Crossover)
# -------------------------------
def crossover(p1, p2):
    cut = random.randint(0, len(p1) - 1)
    child = p1[:cut] + p2[cut:]
    return child

# -------------------------------
# การกลายพันธุ์ (Mutation)
# -------------------------------
def mutate(schedule, rate=0.05):
    for i in range(len(schedule)):
        if random.random() < rate:
            schedule[i] = create_gene()
    return schedule

# -------------------------------
# วนรอบหลักของ GA
# -------------------------------
def run_ga(generations=100, population_size=20):
    population = create_population(population_size)

    for g in range(generations):
        population = sorted(population, key=fitness, reverse=True)
        best = population[0]
        print(f"Generation {g+1}: Best Fitness = {fitness(best)}")

        # ถ้าดีมากพอแล้ว หยุดเลย
        if fitness(best) >= 950:
            break

        new_population = []
        for _ in range(population_size):
            p1, p2 = selection(population)
            child = crossover(random.choice(p1), random.choice(p2))
            child = mutate(child)
            new_population.append(child)
        population = new_population

    return population[0]

# -------------------------------
# เริ่มทำงาน
# -------------------------------
best_schedule = run_ga()

# -------------------------------
# บันทึกผลลัพธ์เป็น CSV
# -------------------------------
output = pd.DataFrame(best_schedule)
output.to_csv(DATASET_PATH + "timetableoutput.csv", index=False, encoding="utf-8-sig")

print("\n✅ สร้างตารางสอนสำเร็จ -> บันทึกที่ dataset/timetableoutput.csv")
