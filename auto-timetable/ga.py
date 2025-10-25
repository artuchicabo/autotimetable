import random
import csv

# ====== ข้อมูลพื้นฐาน ======
teachers = ['ครู A', 'ครู B', 'ครู C', 'ครู D']
subjects = ['Math', 'Science', 'English', 'History']
rooms = ['A101', 'B201', 'C301', 'D401']
times = [8, 9, 10, 11]  # ชั่วโมงเรียน
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday']  # จำนวนวันเรียน

population_size = 30
generations = 100
mutation_rate = 0.3

# ====== สร้างโครโมโซม ======
def create_individual():
    schedule = []
    for day in days:
        for subj in subjects:
            schedule.append({
                'day': day,
                'subject': subj,
                'teacher': random.choice(teachers),
                'room': random.choice(rooms),
                'time': random.choice(times)
            })
    return schedule

# ====== Fitness Function ======
def fitness(individual):
    score = 0
    teacher_times = {}
    room_times = {}

    for cls in individual:
        t_key = (cls['teacher'], cls['day'], cls['time'])
        r_key = (cls['room'], cls['day'], cls['time'])
        if t_key not in teacher_times:
            teacher_times[t_key] = 1
        else:
            score -= 2  # ครูซ้อนเวลา
        if r_key not in room_times:
            room_times[r_key] = 1
        else:
            score -= 2  # ห้องซ้ำเวลา

    # เวลาเรียนไม่ซ้ำในแต่ละวัน
    for day in days:
        times_set = set()
        for cls in individual:
            if cls['day'] == day:
                if cls['time'] not in times_set:
                    times_set.add(cls['time'])
                else:
                    score -= 1  # เวลาเรียนซ้ำ
    return score

# ====== GA: Selection, Crossover, Mutation ======
def select_pair(population):
    sorted_pop = sorted(population, key=lambda x: fitness(x), reverse=True)
    return sorted_pop[0], sorted_pop[1]

def crossover(parent1, parent2):
    child = []
    for i in range(len(parent1)):
        child.append(parent1[i] if random.random() < 0.5 else parent2[i])
    return child

def mutate(individual):
    for cls in individual:
        if random.random() < mutation_rate:
            cls['teacher'] = random.choice(teachers)
            cls['room'] = random.choice(rooms)
            cls['time'] = random.choice(times)
    return individual

# ====== สร้างประชากรเริ่มต้น ======
population = [create_individual() for _ in range(population_size)]

# ====== เริ่มรัน GA ======
for gen in range(generations):
    new_population = []
    for _ in range(population_size // 2):
        parent1, parent2 = select_pair(population)
        child1 = mutate(crossover(parent1, parent2))
        child2 = mutate(crossover(parent1, parent2))
        new_population.extend([child1, child2])
    population = new_population
    
    best_gen = max(population, key=lambda x: fitness(x))
    print(f"Generation {gen+1} | Best Fitness = {fitness(best_gen)}")

# ====== แสดงตารางเรียนดีที่สุด ======
best = max(population, key=lambda x: fitness(x))
print("\n=== ตารางเรียนที่ดีที่สุด ===")
for cls in best:
    print(f"{cls['day']} | {cls['subject']} | {cls['teacher']} | {cls['room']} | {cls['time']}:00")

# ====== Export CSV ======
with open('schedule_full.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Day', 'Subject', 'Teacher', 'Room', 'Time'])
    for cls in best:
        writer.writerow([cls['day'], cls['subject'], cls['teacher'], cls['room'], f"{cls['time']}:00"])

print("\nตารางเรียนถูกบันทึกเป็น schedule_full.csv แล้ว สามารถเปิดใน Excel/Google Sheets ได้")
