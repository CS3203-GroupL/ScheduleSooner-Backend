# scheduler.py (final with input pre-splitting)

import json
import os
import re
import requests
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime

# === Step 0: Ensure output folder exists ===
output_folder = "saved_courses"
os.makedirs(output_folder, exist_ok=True)

# === Step 1: Load TinyLlama-1.1B-Chat ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map="auto",
    trust_remote_code=True
).eval()

# === Step 2: Get Courses ===
def get_courses(filter_type: str, filter_value: str):
    login_url = "https://schedulesooner-backend.onrender.com/api/login/"
    login_data = {
        "username": os.getenv("SCHEDULE_USERNAME"),
        "password": os.getenv("SCHEDULE_PASSWORD")
    }

    res = requests.post(login_url, json=login_data)
    access_token = res.json()["access"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = "https://schedulesooner-backend.onrender.com/cs/courses/"
    params = {filter_type: filter_value}

    all_results = []

    while url:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        all_results.extend(data.get("results", []))
        url = data.get("next")
        params = {}

    return all_results

# === Step 3: Regex-First Parsing ===
def regex_parse_preferences(user_input, courses_data):
    parsed = {}

    course_codes = re.findall(r'\bCS\s*\d{4}\b', user_input, flags=re.IGNORECASE)
    course_codes = [code.replace(' ', '') for code in course_codes]

    if course_codes:
        parsed["courses"] = [{"course": code} for code in course_codes]

    meeting_days_match = re.search(r'\b(MWF|TR|MW|WF|TTH|TH)\b', user_input, flags=re.IGNORECASE)
    if meeting_days_match:
        parsed["meeting_days"] = meeting_days_match.group(0).upper()

    meeting_time_match = re.search(r'\b(\d{1,2}:\d{2}\s*[APMapm]{2})\b', user_input)
    if meeting_time_match:
        parsed["meeting_time"] = meeting_time_match.group(1).lower()

    matched_titles = []
    for entry in courses_data:
        title = entry.get("title", "").lower()
        if title and title in user_input.lower():
            matched_titles.append(entry.get("title"))

    if matched_titles:
        if "courses" not in parsed:
            parsed["courses"] = []
        for title in matched_titles:
            parsed["courses"].append({"title": title})

    instructor_match = re.search(r'with ([A-Za-z\s]+)', user_input)
    if instructor_match:
        instructor_name = instructor_match.group(1).strip()
        parsed["instructor"] = instructor_name

    if not parsed:
        print("⚠️ Complex input detected, falling back to LLM parsing...")
        parsed = parse_preferences_with_llm(user_input)

    return parsed

# === Step 4: TinyLlama Fallback Parsing ===
def parse_preferences_with_llm(user_input):
    print("AI TIME BABYYYY")
    few_shot = """
You are an assistant that extracts course preferences from user input.
✅ Only extract fields that are explicitly mentioned.
✅ DO NOT guess missing fields like meeting_time or instructor unless stated.

Allowed fields: "course", "title", "instructor", "meeting_days", "meeting_time"

Examples:
Input: "I want any courses with Neeman on MWF."
Output: {"instructor": "Neeman", "meeting_days": "MWF"}

Input: "I want to take CS 2614 and Software Engineering on MWF."
Output: {"course": "CS 2614", "title": "Software Engineering", "meeting_days": "MWF"}

Input: "I want to take TR classes."
Output: {"meeting_days": "TR"}
"""

    prompt = f"""{few_shot}

Input: "{user_input}"
Output:
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            pad_token_id=tokenizer.eos_token_id
        )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    try:
        json_blocks = re.findall(r"{.*?}", decoded, re.DOTALL)
        if not json_blocks:
            raise ValueError("No JSON found.")
        last_json = json_blocks[-1]
        parsed = json.loads(last_json)
        return parsed
    except Exception as e:
        print(f"❌ Error parsing LLM output: {e}")
        print("🔴 Full raw output:\n", decoded)
        return {}

# === Step 5: Pre-split messy input ===
def pre_split_user_input(user_input):
    user_input = user_input.replace('&', 'and')
    pieces = re.split(r'\band\b', user_input, flags=re.IGNORECASE)

    if len(pieces) == 1:
        return [user_input.strip()]

    prefix = pieces[0].strip()
    result = []
    for suffix in pieces[1:]:
        piece = f"{prefix} and {suffix.strip()}"
        result.append(piece.strip())

    return result

# === Step 6: Main Program ===
user_input = input("Describe your course preferences:\n> ").strip()

courses_data = get_courses("subject", "C S")
if "results" in courses_data:
    courses_data = courses_data["results"]

with open(os.path.join(output_folder, "courses_output.json"), "w") as f:
    json.dump(courses_data, f, indent=2)

# Pre-process user input
split_inputs = pre_split_user_input(user_input)

parsed_preferences = {}
for sub_input in split_inputs:
    parsed_piece = regex_parse_preferences(sub_input, courses_data)
    for key, value in parsed_piece.items():
        if key not in parsed_preferences:
            parsed_preferences[key] = value
        else:
            if isinstance(parsed_preferences[key], list) and isinstance(value, list):
                parsed_preferences[key].extend(value)
            elif isinstance(parsed_preferences[key], str) and isinstance(value, str):
                parsed_preferences[key] = f"{parsed_preferences[key]} and {value}"

if not parsed_preferences:
    print("⚠️ No preferences parsed from input. Exiting.")
    exit()

# === Step 7: Validate Preferences ===
validated_preferences = {}

for course_item in parsed_preferences.get("courses", []):
    if "course" in course_item:
        course_number = re.sub(r'[^0-9]', '', course_item["course"])
        matched = next((entry for entry in courses_data if entry.get("course") == course_number), None)
        if matched:
            validated_preferences.setdefault("courses", []).append({"course": course_number})
        else:
            print(f"⚠️ Course '{course_item['course']}' (parsed as '{course_number}') not found in catalog.")
    if "title" in course_item:
        matched = next((entry for entry in courses_data if entry.get("title", "").lower() == course_item["title"].lower()), None)
        if matched:
            validated_preferences.setdefault("courses", []).append({"course": matched.get("course")})

for key in ["instructor", "meeting_days", "meeting_time"]:
    if key in parsed_preferences:
        validated_preferences[key] = parsed_preferences[key]

# === Step 8: Fetch and Save Filtered Results ===
for filter_type, filter_value in validated_preferences.items():
    if filter_type == "courses":
        for course in filter_value:
            course_number = course["course"]
            safe_val = re.sub(r'\W+', '_', course_number)
            course_results = get_courses("course", course_number)
            with open(os.path.join(output_folder, f"course_{safe_val}.json"), "w") as f:
                json.dump(course_results, f, indent=2)
            print(f"💾 Saved course_{safe_val}.json")
    else:
        safe_val = re.sub(r'\W+', '_', str(filter_value))
        results = get_courses(filter_type, filter_value)
        with open(os.path.join(output_folder, f"{filter_type}_{safe_val}.json"), "w") as f:
            json.dump(results, f, indent=2)
        print(f"💾 Saved {filter_type}_{safe_val}.json")

# === Step 9: Merge Saved Courses ===
def merge_saved_courses():
    all_courses = []
    seen = set()

    for filename in os.listdir(output_folder):
        if filename.endswith(".json") and filename != "courses_output.json":
            file_path = os.path.join(output_folder, filename)
            with open(file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    data = [data]
                for entry in data:
                    unique_key = entry.get("crn") or entry.get("id")
                    if unique_key and unique_key not in seen:
                        seen.add(unique_key)
                        all_courses.append(entry)

    with open("all_unique_courses.json", "w") as f:
        json.dump(all_courses, f, indent=2)
    print(f"✅ Merged {len(all_courses)} unique course entries into all_unique_courses.json")

    # Cleanup
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print(f"🧹 Cleaned up all files in '{output_folder}' after merge.")

merge_saved_courses()
