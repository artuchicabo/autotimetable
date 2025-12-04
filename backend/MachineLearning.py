"""
AI Scheduling - Genetic Algorithm for Timetable Generation
OPTIMIZED VERSION - Faster execution with reduced parameters
"""

import pandas as pd
import random
import copy
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

def _path(name):
    return os.path.join(DATASET_DIR, name)

# Global status for progress tracking
scheduling_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'result': None,
    'error': None
}

def run_scheduling(progress_callback=None):
    """
    Run GA scheduling algorithm - OPTIMIZED for speed
    Returns: dict with status and result
    """
    global scheduling_status
    
    try:
        scheduling_status['running'] = True
        scheduling_status['progress'] = 0
        scheduling_status['message'] = 'Loading data...'
        scheduling_status['error'] = None
        
        # ============================================================
        # LOAD DATA
        # ============================================================
        from data_loader import (
            load_subjects, load_teachers, load_rooms, 
            load_groups, load_timeslots
        )
        
        subjects = load_subjects()
        teachers = load_teachers()
        rooms = load_rooms()
        groups = load_groups()
        timeslot_obj = load_timeslots()
        
        teach = pd.read_csv(_path("teach.csv"))
        register = pd.read_csv(_path("register.csv"))
        
        # Remove empty rows
        teach = teach.dropna(how='all')
        register = register.dropna(how='all')
        
        scheduling_status['message'] = 'Preparing constraints...'
        scheduling_status['progress'] = 5
        
        # ============================================================
        # PREPARE GLOBAL REFERENCES
        # ============================================================
        
        # Mapping subject -> teachers (as dict for faster lookup)
        subject_teachers = {}
        for _, row in teach.iterrows():
            sid = row["subject_id"]
            tid = row["teacher_id"]
            if sid not in subject_teachers:
                subject_teachers[sid] = []
            subject_teachers[sid].append(tid)
        
        # Hours per subject
        subject_hours = {sid: (subj.theory + subj.practice) for sid, subj in subjects.items()}
        
        # Group-subject-hours from register
        group_subjects = []
        for _, row in register.iterrows():
            g = row["group_id"]
            s = row["subject_id"]
            h = subject_hours.get(s, 0)
            if h > 0:
                group_subjects.append((g, s, h))
        
        # Required hours
        required_hours = {(g, s): int(h) for g, s, h in group_subjects}
        
        # Expected subjects per group
        expected_subjects_by_group = {
            g: set(rows["subject_id"].tolist())
            for g, rows in register.groupby("group_id")
        }
        
        # Total hours
        expected_total_hours = sum(required_hours.values())
        
        # ============================================================
        # VALID TIMESLOTS (exclude period 5 - lunch break, and > 10)
        # ============================================================
        
        teaching_slots = [
            (ts.day, ts.period)
            for ts in timeslot_obj.values()
            if ts.period != 5 and ts.period <= 10
        ]
        
        # Pre-compute timeslot mapping
        timeslot_lookup = {
            (ts.day, ts.period): ts.timeslot_id
            for ts in timeslot_obj.values()
        }
        
        room_list = list(rooms.keys())
        
        # ============================================================
        # OPTIMIZED RANDOM SCHEDULE - Greedy with constraints
        # ============================================================
        
        def random_schedule():
            schedule = []
            teacher_busy = set()  # (teacher, day, period)
            room_busy = set()     # (room, day, period)
            group_busy = set()    # (group, day, period)
            group_day_load = {}   # (group, day) -> count
            
            # Shuffle for randomness
            shuffled_gs = list(group_subjects)
            random.shuffle(shuffled_gs)
            
            for g, s, hours in shuffled_gs:
                teachers_allowed = subject_teachers.get(s, [])
                if not teachers_allowed:
                    continue
                
                slots_needed = int(hours)
                slots_assigned = 0
                
                # Try to find consecutive slots first
                # Group available slots by day
                day_slots = {}
                for d, p in teaching_slots:
                    if d not in day_slots:
                        day_slots[d] = []
                    day_slots[d].append(p)
                
                # Sort periods for each day
                for d in day_slots:
                    day_slots[d].sort()
                
                # Shuffle days to try
                days_to_try = list(day_slots.keys())
                random.shuffle(days_to_try)
                
                # 1. Try to schedule as a single block or large chunks
                for day in days_to_try:
                    if slots_assigned >= slots_needed:
                        break
                        
                    periods = day_slots[day]
                    # Find consecutive sequences
                    sequences = []
                    if not periods: continue
                    
                    current_seq = [periods[0]]
                    for i in range(1, len(periods)):
                        if periods[i] == periods[i-1] + 1:
                            current_seq.append(periods[i])
                        else:
                            sequences.append(current_seq)
                            current_seq = [periods[i]]
                    sequences.append(current_seq)
                    
                    # Try to fit in sequences
                    random.shuffle(sequences)
                    
                    for seq in sequences:
                        if slots_assigned >= slots_needed:
                            break
                            
                        # How many slots can we take from this sequence?
                        # We want as many as possible up to slots_needed - slots_assigned
                        remaining_needed = slots_needed - slots_assigned
                        
                        # Try different start points in the sequence
                        possible_starts = []
                        for i in range(len(seq)):
                            # Check max length we can grab from here
                            max_len = min(len(seq) - i, remaining_needed)
                            if max_len > 0:
                                possible_starts.append((i, max_len))
                        
                        random.shuffle(possible_starts)
                        
                        for start_idx, length in possible_starts:
                            # Check if these slots are valid
                            proposed_periods = seq[start_idx : start_idx + length]
                            
                            # Check constraints for all proposed periods
                            valid_block = True
                            
                            # Check group day load
                            if group_day_load.get((g, day), 0) + length > 10:
                                continue
                                
                            # Check availability
                            for p in proposed_periods:
                                if (g, day, p) in group_busy:
                                    valid_block = False
                                    break
                            
                            if not valid_block:
                                continue
                                
                            # Find a teacher and room available for ALL periods in block
                            random.shuffle(teachers_allowed)
                            found_teacher_room = False
                            
                            for t in teachers_allowed:
                                # Check teacher availability for all periods
                                teacher_ok = True
                                for p in proposed_periods:
                                    if (t, day, p) in teacher_busy:
                                        teacher_ok = False
                                        break
                                if not teacher_ok:
                                    continue
                                    
                                # Find room available for all periods
                                random.shuffle(room_list)
                                for room in room_list:
                                    room_ok = True
                                    for p in proposed_periods:
                                        if (room, day, p) in room_busy:
                                            room_ok = False
                                            break
                                    
                                    if room_ok:
                                        # ASSIGN BLOCK
                                        for p in proposed_periods:
                                            schedule.append({
                                                "group_id": g,
                                                "day": day,
                                                "period": p,
                                                "subject_id": s,
                                                "teacher_id": t,
                                                "room_id": room
                                            })
                                            teacher_busy.add((t, day, p))
                                            room_busy.add((room, day, p))
                                            group_busy.add((g, day, p))
                                            group_day_load[(g, day)] = group_day_load.get((g, day), 0) + 1
                                            slots_assigned += 1
                                        
                                        found_teacher_room = True
                                        break
                                
                                if found_teacher_room:
                                    break
                            
                            if found_teacher_room:
                                break # Move to next sequence/day if we filled some slots
                
                # 2. Fallback: Fill remaining slots individually (randomly) if block scheduling failed
                if slots_assigned < slots_needed:
                    available_slots = list(teaching_slots)
                    random.shuffle(available_slots)
                    
                    for day, period in available_slots:
                        if slots_assigned >= slots_needed:
                            break
                        
                        if group_day_load.get((g, day), 0) >= 10:
                            continue
                        
                        if (g, day, period) in group_busy:
                            continue
                        
                        random.shuffle(teachers_allowed)
                        for t in teachers_allowed:
                            if (t, day, period) in teacher_busy:
                                continue
                            
                            random.shuffle(room_list)
                            for room in room_list:
                                if (room, day, period) in room_busy:
                                    continue
                                
                                schedule.append({
                                    "group_id": g,
                                    "day": day,
                                    "period": period,
                                    "subject_id": s,
                                    "teacher_id": t,
                                    "room_id": room
                                })
                                teacher_busy.add((t, day, period))
                                room_busy.add((room, day, period))
                                group_busy.add((g, day, period))
                                group_day_load[(g, day)] = group_day_load.get((g, day), 0) + 1
                                slots_assigned += 1
                                break
                            else:
                                continue
                            break
            
            return schedule
        
        # ============================================================
        # FAST FITNESS FUNCTION
        # ============================================================
        
        def fitness(schedule):
            if not schedule:
                return -1e9
            
            score = 0
            teacher_slots = {}
            room_slots = {}
            group_slots = {}
            group_subject_count = {}
            group_day_count = {}
            
            # Track subject slots per group per day for fragmentation check
            # (group, day, subject) -> list of periods
            group_day_subject_periods = {}
            
            for e in schedule:
                t, d, p = e["teacher_id"], e["day"], e["period"]
                r, g, s = e["room_id"], e["group_id"], e["subject_id"]
                
                # Check conflicts
                tk = (t, d, p)
                rk = (r, d, p)
                gk = (g, d, p)
                
                if tk in teacher_slots:
                    score -= 100
                else:
                    teacher_slots[tk] = True
                    score += 1
                
                if rk in room_slots:
                    score -= 100
                else:
                    room_slots[rk] = True
                
                if gk in group_slots:
                    score -= 100
                else:
                    group_slots[gk] = True
                
                # Count group-subject hours
                gs_key = (g, s)
                group_subject_count[gs_key] = group_subject_count.get(gs_key, 0) + 1
                
                # Count group-day load
                gd_key = (g, d)
                group_day_count[gd_key] = group_day_count.get(gd_key, 0) + 1
                
                # Track for fragmentation check
                gds_key = (g, d, s)
                if gds_key not in group_day_subject_periods:
                    group_day_subject_periods[gds_key] = []
                group_day_subject_periods[gds_key].append(p)
                
                # Penalty for period 5 or > 10
                if p == 5:
                    score -= 1000
                if p > 10:
                    score -= 1000
            
            # Check hours match
            for key, req in required_hours.items():
                actual = group_subject_count.get(key, 0)
                score -= abs(actual - req) * 30
            
            # Check total hours
            score -= abs(len(schedule) - expected_total_hours) * 20
            
            # Check day load <= 10
            for gd, cnt in group_day_count.items():
                if cnt > 10:
                    score -= (cnt - 10) * 500
            
            # Check fragmentation and consecutive bonus
            for gds_key, periods in group_day_subject_periods.items():
                periods.sort()
                
                # If multiple periods for same subject on same day
                if len(periods) > 1:
                    # Check if they are consecutive
                    is_consecutive = True
                    for i in range(len(periods) - 1):
                        if periods[i+1] != periods[i] + 1:
                            is_consecutive = False
                            break
                    
                    if is_consecutive:
                        # Bonus for consecutive blocks
                        score += len(periods) * 20  # Increased bonus
                    else:
                        # Penalty for fragmentation (e.g. period 1 and 3)
                        score -= 50  # Significant penalty
            
            return score
        
        # ============================================================
        # FAST MUTATION
        # ============================================================
        
        def mutate(schedule):
            if len(schedule) < 2:
                return
            
            idx = random.randint(0, len(schedule) - 1)
            entry = schedule[idx]
            
            # Try new timeslot
            new_day, new_period = random.choice(teaching_slots)
            entry["day"] = new_day
            entry["period"] = new_period
        
        # ============================================================
        # CHECK CONSTRAINTS
        # ============================================================
        
        def is_valid(schedule):
            if len(schedule) != expected_total_hours:
                return False
            
            teacher_slots = set()
            room_slots = set()
            group_slots = set()
            group_subject_count = {}
            group_day_count = {}
            
            for e in schedule:
                t, d, p = e["teacher_id"], e["day"], e["period"]
                r, g, s = e["room_id"], e["group_id"], e["subject_id"]
                
                if p == 5 or p > 10:
                    return False
                
                tk = (t, d, p)
                rk = (r, d, p)
                gk = (g, d, p)
                
                if tk in teacher_slots or rk in room_slots or gk in group_slots:
                    return False
                
                teacher_slots.add(tk)
                room_slots.add(rk)
                group_slots.add(gk)
                
                gs_key = (g, s)
                group_subject_count[gs_key] = group_subject_count.get(gs_key, 0) + 1
                
                gd_key = (g, d)
                group_day_count[gd_key] = group_day_count.get(gd_key, 0) + 1
            
            # Check hours
            for key, req in required_hours.items():
                if group_subject_count.get(key, 0) != req:
                    return False
            
            # Check day load
            for gd, cnt in group_day_count.items():
                if cnt > 10:
                    return False
            
            return True
        
        # ============================================================
        # GA - OPTIMIZED PARAMETERS
        # ============================================================
        
        POPULATION_SIZE = 40  # Reduced from 80
        GENERATIONS = 150     # Reduced from 300
        NUM_RUNS = 5          # Reduced from 15
        ELITE_COUNT = 8
        MUTATION_RATE = 0.35
        
        overall_best = None
        overall_best_score = float("-inf")
        
        for run in range(NUM_RUNS):
            scheduling_status['message'] = f'Running GA: Round {run + 1}/{NUM_RUNS}'
            scheduling_status['progress'] = 10 + int((run / NUM_RUNS) * 80)
            
            # Initialize population
            population = [random_schedule() for _ in range(POPULATION_SIZE)]
            
            for gen in range(GENERATIONS):
                # Evaluate and sort
                scored = [(s, fitness(s)) for s in population]
                scored.sort(key=lambda x: x[1], reverse=True)
                
                best_schedule, best_score = scored[0]
                
                # Check if valid
                if is_valid(best_schedule):
                    if best_score > overall_best_score:
                        overall_best = copy.deepcopy(best_schedule)
                        overall_best_score = best_score
                    break
                
                # Keep if better than overall
                if best_score > overall_best_score:
                    overall_best = copy.deepcopy(best_schedule)
                    overall_best_score = best_score
                
                # Selection - elite
                next_gen = [copy.deepcopy(s) for s, _ in scored[:ELITE_COUNT]]
                
                # Crossover and mutation
                while len(next_gen) < POPULATION_SIZE:
                    p1, _ = random.choice(scored[:20])
                    p2, _ = random.choice(scored[:20])
                    
                    if len(p1) > 0 and len(p2) > 0:
                        cut = random.randint(0, min(len(p1), len(p2)))
                        child = copy.deepcopy(p1[:cut]) + copy.deepcopy(p2[cut:])
                        
                        if random.random() < MUTATION_RATE:
                            mutate(child)
                        
                        next_gen.append(child)
                    else:
                        next_gen.append(random_schedule())
                
                population = next_gen
        
        # ============================================================
        # EXPORT RESULT
        # ============================================================
        
        if overall_best is None or len(overall_best) == 0:
            scheduling_status['running'] = False
            scheduling_status['progress'] = 100
            scheduling_status['message'] = 'Failed to generate schedule'
            scheduling_status['result'] = None
            return {'status': 'FAILED', 'message': 'Could not generate valid schedule'}
        
        scheduling_status['message'] = 'Saving results...'
        scheduling_status['progress'] = 95
        
        # Add timeslot_id
        for entry in overall_best:
            entry["timeslot_id"] = timeslot_lookup.get((entry["day"], entry["period"]), None)
        
        df = pd.DataFrame(overall_best)
        df = df[[
            "group_id",
            "timeslot_id", 
            "subject_id",
            "teacher_id",
            "room_id"
        ]].sort_values(["group_id", "timeslot_id"])
        
        # Save to files
        output_path = _path("timetable.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        root_output = os.path.join(BASE_DIR, "timetable.csv")
        df.to_csv(root_output, index=False, encoding="utf-8-sig")
        
        scheduling_status['running'] = False
        scheduling_status['progress'] = 100
        scheduling_status['message'] = 'Schedule generated successfully!'
        scheduling_status['result'] = {
            'total_slots': len(df),
            'fitness_score': overall_best_score
        }
        
        return {
            'status': 'SUCCESS',
            'message': 'Schedule generated successfully',
            'data': {
                'total_slots': len(df),
                'fitness_score': overall_best_score
            }
        }
        
    except Exception as e:
        import traceback
        scheduling_status['running'] = False
        scheduling_status['progress'] = 0
        scheduling_status['message'] = f'Error: {str(e)}'
        scheduling_status['error'] = str(e)
        print(traceback.format_exc())
        return {'status': 'ERROR', 'message': str(e)}

def get_status():
    """Get current scheduling status"""
    return scheduling_status

if __name__ == "__main__":
    print("Starting AI Scheduling...")
    result = run_scheduling()
    print(f"Result: {result}")
