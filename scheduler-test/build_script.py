
import json
import itertools
import copy
import re
import requests

def load_courses(filename="all_unique_courses.json"):
    with open(filename, "r") as f:
        courses = json.load(f)
    return courses

def parse_meeting_time(meeting_time):
    try:
        start_str, end_str = meeting_time.lower().split(" - ")
        start_minutes = time_str_to_minutes(start_str)
        end_minutes = time_str_to_minutes(end_str)
        return start_minutes, end_minutes
    except Exception:
        return None, None

def time_str_to_minutes(timestr):
    match = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)", timestr.strip())
    if not match:
        return None
    hour, minute, period = match.groups()
    hour = int(hour)
    minute = int(minute)
    if period == "pm" and hour != 12:
        hour += 12
    if period == "am" and hour == 12:
        hour = 0
    return hour * 60 + minute

def check_conflict(existing_classes, new_class):
    if "meeting_days" not in new_class or "meeting_time" not in new_class:
        return False

    new_days = set(new_class["meeting_days"])
    start_new, end_new = parse_meeting_time(new_class["meeting_time"])
    if start_new is None or end_new is None:
        return False

    for cls in existing_classes:
        cls_days = set(cls["meeting_days"])
        if not new_days.intersection(cls_days):
            continue
        start_existing, end_existing = parse_meeting_time(cls["meeting_time"])
        if start_existing is None or end_existing is None:
            continue
        if start_new < end_existing and start_existing < end_new:
            return True
    return False

def build_schedule(courses, max_classes=5):
    grouped = {}
    for course in courses:
        key = f"{course['subject']} {course['course']}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(course)

    selected = []
    for course_key, sections in grouped.items():
        found = False
        for section in sections:
            if not check_conflict(selected, section):
                selected.append(copy.deepcopy(section))
                found = True
                break
        if found and len(selected) >= max_classes:
            break
    return selected

def save_schedule(schedule, filename="final_schedule.json"):
    with open(filename, "w") as f:
        json.dump(schedule, f, indent=2)
    print(f"💾 Saved final schedule to {filename}")


def main():
    print(f"📚 Loading courses from all_unique_courses.json...")
    courses = load_courses()

    print(f"🛠 Building one valid, no-conflict schedule...")
    schedule = build_schedule(courses, max_classes=5)

    if not schedule:
        print("⚠️ Could not build any valid schedule.")
    else:
        save_schedule(schedule)
    
    url = 'https://schedulesooner-backend.onrender.com/api/upload-file/'
    file_path = 'final_schedule.json'  # Path to the file on your machine

    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        response = requests.post(url, files=files)

    print("Status Code:", response.status_code)
    print("Response:", response.text)

if __name__ == "__main__":
    main()

