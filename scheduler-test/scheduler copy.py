import json
import os
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import requests
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

        all_results.extend(data.get("results", []))  # Append this page's results

        url = data.get("next")  # Next page URL
        params = {}  # Only use params on first request!

    return all_results

# === Step 3: Parse Preferences from User Input ===
def parse_preferences_with_llm(user_input):
    few_shot = few_shot = """
You are an assistant that extracts course preferences from user input.

✅ Only extract fields that are clearly mentioned.
✅ If a time is NOT mentioned, DO NOT guess meeting_time.
✅ If an instructor is mentioned, extract it.
✅ If days are mentioned, extract them.
✅ DO NOT invent missing fields!

Allowed fields: "course", "title", "instructor", "meeting_days", "meeting_time"

⚠️ If the user does not mention meeting_time, DO NOT include meeting_time.
⚠️ If the user does not mention an instructor, DO NOT include instructor.

Examples:

Input: "I want to take CS 2614 and Software Engineering."
Output: {"course": "CS 2614", "title": "Software Engineering"}

Input: "I want any courses with Neeman on MWF."
Output: {"instructor": "Neeman", "meeting_days": "MWF"}

Input: "I want to take TR classes with Atiquzzaman."
Output: {"meeting_days": "TR", "instructor": "Atiquzzaman"}
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
    print("🔵 Raw model output:\n", decoded)

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

# === Step 4: Main Execution ===
user_input = input("Describe your course preferences:\n> ").strip()

parsed_preferences = parse_preferences_with_llm(user_input)

if not parsed_preferences:
    print("⚠️ No preferences parsed from input. Exiting.")
    exit()

# === Step 5: Fetch All C S Courses ===
print("🌐 Fetching all Computer Science courses...")
courses_data = get_courses("subject", "C S")

# If it's wrapped in results, fix it:
if "results" in courses_data:
    courses_data = courses_data["results"]

# Save full CS courses for backup
with open(os.path.join(output_folder, "courses_output.json"), "w") as f:
    json.dump(courses_data, f, indent=2)

print(f"✅ Loaded {len(courses_data)} CS courses.")

# === Step 6: Build Validation Sets ===
valid_courses = set()
valid_titles = set()

for entry in courses_data:
    if isinstance(entry, dict):
        if 'course' in entry:
            valid_courses.add(entry['course'])
        if 'title' in entry:
            valid_titles.add(entry['title'].lower())

# === Step 7: Validate Preferences ===
validated_preferences = {}

# === 7.1 Extract and Correct Courses ===
def extract_course_number(course_str):
    return ''.join(re.findall(r'\d+', course_str))

def find_course_title(course_number, courses_data):
    for entry in courses_data:
        if entry.get("course") == course_number:
            return entry.get("title")
    return None

validated_courses = []

original_courses = parsed_preferences.get("course")
if original_courses:
    courses = re.split(r',|\band\b', original_courses)
    courses = [c.strip() for c in courses if c.strip()]

    for course_text in courses:
        course_number = extract_course_number(course_text)
        title = find_course_title(course_number, courses_data)

        if course_number and title:
            validated_courses.append({
                "course": course_number,
                "title": title
            })
        else:
            print(f"⚠️ No valid match found for '{course_text}'")

if validated_courses:
    validated_preferences["courses"] = validated_courses

# === 7.2 Validate Instructor, Meeting Days, Time ===
for key in ["instructor", "meeting_days", "meeting_time"]:
    if key in parsed_preferences:
        validated_preferences[key] = parsed_preferences[key]

# === Step 8: Fetch and Save Final Filtered Results ===
for filter_type, filter_value in validated_preferences.items():
    if filter_type == "courses":
        for course in filter_value:
            course_results = get_courses("course", course)

            safe_val = re.sub(r'\W+', '_', course["course"])
            with open(os.path.join(output_folder, f"course_{safe_val}.json"), "w") as f:
                json.dump(course_results, f, indent=2)
            print(f"💾 Saved course_{safe_val}.json")

    else:
        preference_results = get_courses(filter_type, filter_value)

        safe_val = re.sub(r'\W+', '_', course["course"])
        with open(os.path.join(output_folder, f"{filter_type}_{safe_val}.json"), "w") as f:
            json.dump(preference_results, f, indent=2)
        print(f"💾 Saved {filter_type}_{safe_val}.json")

# === Step 9: Merge all saved JSONs into one unique file ===

def merge_saved_courses():
    input_folder = "saved_courses"
    output_file = "all_unique_courses.json"

    all_courses = []
    seen = set()

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            if filename == "courses_output.json":
                continue  # 🚫 Skip the full backup file

            file_path = os.path.join(input_folder, filename)

            with open(file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️ Skipping invalid JSON file: {filename}")
                    continue

                if isinstance(data, dict):
                    data = [data]
                elif not isinstance(data, list):
                    print(f"⚠️ Skipping non-list file: {filename}")
                    continue

                for entry in data:
                    unique_key = entry.get("crn") or entry.get("id")

                    if unique_key and unique_key not in seen:
                        seen.add(unique_key)
                        all_courses.append(entry)

    with open(output_file, "w") as f:
        json.dump(all_courses, f, indent=2)

    print(f"✅ Merged {len(all_courses)} unique course entries into {output_file}")
    # === Step 10: Cleanup after merge ===
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Could not delete {file_path}: {e}")

    print(f"🧹 Cleaned up all files in '{input_folder}' after merge.")
        
# === Finally, run merge automatically ===
merge_saved_courses()