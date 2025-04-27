
import json
import itertools
from datetime import datetime

def load_courses(filename="all_unique_courses.json"):
    with open(filename, "r") as f:
        courses = json.load(f)
    return courses

def group_courses(courses):
    grouped = {}
    for course in courses:
        key = f"{course['subject']} {course['course']}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(course)
    return grouped

def time_to_minutes(timestr):
    hours, minutes = map(int, timestr.split(":"))
    return hours * 60 + minutes

def check_time_conflict(class1, class2):
    days1 = set(class1["meeting_days"])
    days2 = set(class2["meeting_days"])
    if not days1.intersection(days2):
        return False  # No common days, no conflict

    start1 = time_to_minutes(class1["start_time"])
    end1 = time_to_minutes(class1["end_time"])
    start2 = time_to_minutes(class2["start_time"])
    end2 = time_to_minutes(class2["end_time"])

    return start1 < end2 and start2 < end1

def is_valid_schedule(combo):
    for i in range(len(combo)):
        for j in range(i + 1, len(combo)):
            if check_time_conflict(combo[i], combo[j]):
                return False
    return True

def find_valid_schedules(grouped_courses, max_results=5):
    all_groups = list(grouped_courses.values())
    combos = itertools.product(*all_groups)

    valid_schedules = []
    for combo in combos:
        if is_valid_schedule(combo):
            valid_schedules.append(combo)
            if len(valid_schedules) >= max_results:
                break
    return valid_schedules

def print_schedule(schedule):
    print("=== Schedule ===")
    for course in schedule:
        print(f"{course['subject']} {course['course']} - {course['title']} | {course['meeting_days']} {course['start_time']}-{course['end_time']}")
    print("")

if __name__ == "__main__":
    print(f"📚 Loading courses from all_unique_courses.json...")
    courses = load_courses()
    grouped = group_courses(courses)

    print(f"🔍 Finding conflict-free schedules...")
    valid_schedules = find_valid_schedules(grouped, max_results=5)

    if not valid_schedules:
        print("⚠️ No valid schedules found.")
    else:
        print(f"✅ Found {len(valid_schedules)} valid schedules!")
        for idx, schedule in enumerate(valid_schedules):
            print(f"\nSchedule #{idx + 1}")
            print_schedule(schedule)
