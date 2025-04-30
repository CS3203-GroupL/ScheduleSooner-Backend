# === subset_fixed_v2.py ===

import json
import os
import re
import requests
import torch
from dotenv import load_dotenv

import build_script

from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime

# === Setup absolute paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SAVED_COURSES_DIR = os.path.join(OUTPUTS_DIR, "saved_courses")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(SAVED_COURSES_DIR, exist_ok=True)

# === Load TinyLlama ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map="auto",
    trust_remote_code=True
).eval()

# === Helper functions ===
def get_courses(filter_type: str, filter_value: str):
    load_dotenv()
    login_url = "https://schedulesooner-backend.onrender.com/api/login/"
    login_data = {"username": os.getenv("SCHEDULE_USERNAME"), "password": os.getenv("SCHEDULE_PASSWORD")}

    res = requests.post(login_url, json=login_data)
    if res.status_code != 200:
        raise Exception(f"Login failed: {res.status_code} {res.text}")

    token_data = res.json()
    if "access" not in token_data:
        raise Exception(f"Unexpected login response: {token_data}")

    headers = {"Authorization": f"Bearer {token_data['access']}"}
    res = requests.get("https://schedulesooner-backend.onrender.com/cs/courses/", headers=headers, params={filter_type: filter_value})

    if res.status_code != 200:
        raise Exception(f"Failed to fetch courses: {res.status_code} {res.text}")

    return res.json()["results"]

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

    matched_titles = [entry.get("title") for entry in courses_data if entry.get("title", "").lower() in user_input.lower()]
    if matched_titles:
        parsed.setdefault("courses", []).extend({"title": title} for title in matched_titles)

    instructor_match = re.search(r'with ([A-Za-z\s]+)', user_input)
    if instructor_match:
        parsed["instructor"] = instructor_match.group(1).strip()

    if not parsed:
        parsed = parse_preferences_with_llm(user_input)

    return parsed

def parse_preferences_with_llm(user_input):
    few_shot = """
You are an assistant that extracts course preferences from user input.
✅ Only extract fields that are explicitly mentioned.
✅ DO NOT guess missing fields like meeting_time or instructor unless stated.
"""
    prompt = f"""{few_shot}\n\nInput: \"{user_input}\"\nOutput:\n"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150, pad_token_id=tokenizer.eos_token_id)

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    try:
        json_blocks = re.findall(r"{.*?}", decoded, re.DOTALL)
        last_json = json_blocks[-1]
        parsed = json.loads(last_json)
        return parsed
    except Exception:
        return {}

def pre_split_user_input(user_input):
    user_input = user_input.replace('&', 'and')
    pieces = re.split(r'\band\b', user_input, flags=re.IGNORECASE)
    if len(pieces) == 1:
        return [user_input.strip()]
    prefix = pieces[0].strip()
    return [f"{prefix} and {suffix.strip()}" for suffix in pieces[1:]]

# === Main Program ===
with open(os.path.join(OUTPUTS_DIR, "user_input.json"), "r") as f:
    user_input = json.load(f).get("user_input")

courses_data = get_courses("subject", "C S")

with open(os.path.join(OUTPUTS_DIR, "courses_output.json"), "w") as f:
    json.dump(courses_data, f, indent=2)

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
    exit()

validated_preferences = {}

for course_item in parsed_preferences.get("courses", []):
    if "course" in course_item:
        course_number = re.sub(r'[^0-9]', '', course_item["course"])
        matched = next((entry for entry in courses_data if entry.get("course") == course_number), None)
        if matched:
            validated_preferences.setdefault("courses", []).append({"course": course_number})
    if "title" in course_item:
        matched = next((entry for entry in courses_data if entry.get("title", "").lower() == course_item["title"].lower()), None)
        if matched:
            validated_preferences.setdefault("courses", []).append({"course": matched.get("course")})

for key in ["instructor", "meeting_days", "meeting_time"]:
    if key in parsed_preferences:
        validated_preferences[key] = parsed_preferences[key]

for filter_type, filter_value in validated_preferences.items():
    if filter_type == "courses":
        for course in filter_value:
            course_number = course["course"]
            safe_val = re.sub(r'\W+', '_', course_number)
            course_results = get_courses("course", course_number)
            with open(os.path.join(SAVED_COURSES_DIR, f"course_{safe_val}.json"), "w") as f:
                json.dump(course_results, f, indent=2)
    else:
        safe_val = re.sub(r'\W+', '_', str(filter_value))
        results = get_courses(filter_type, filter_value)
        with open(os.path.join(SAVED_COURSES_DIR, f"{filter_type}_{safe_val}.json"), "w") as f:
            json.dump(results, f, indent=2)

def merge_saved_courses():
    all_courses = []
    seen = set()

    for filename in os.listdir(SAVED_COURSES_DIR):
        if filename.endswith(".json") and filename != "courses_output.json":
            file_path = os.path.join(SAVED_COURSES_DIR, filename)
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

    final_output_path = os.path.join(OUTPUTS_DIR, "all_unique_courses.json")
    with open(final_output_path, "w") as f:
        json.dump(all_courses, f, indent=2)

    for filename in os.listdir(SAVED_COURSES_DIR):
        os.remove(os.path.join(SAVED_COURSES_DIR, filename))

merge_saved_courses()

build_script.main()

user_input_path = os.path.join(OUTPUTS_DIR, "user_input.json")
if os.path.exists(user_input_path):
    os.remove(user_input_path)
