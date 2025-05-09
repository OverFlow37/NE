import urllib.request
import json
import time
import os
import re

API_URL = "http://localhost:11434/api/generate"

# ==============================
#  서버 호출 함수
# ==============================
import json
import time
import urllib.request


def get_response(prompt: str) -> str:
    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "stream": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    start_time = time.time()
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
    elapsed = time.time() - start_time

    raw_text = raw.decode('utf-8')
    answer = json.loads(raw_text).get("response", "")
    print(f"Response time: {elapsed:.2f} seconds")
    print(f"Response: {answer}")



def save_combined_memory():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reflect_path = os.path.join(base_dir, "reflect", "reflections.json")
    plan_path = os.path.join(base_dir, "plan", "plan.json")
    base_prompt_path = os.path.join(base_dir, "baseprompt.txt")
    output_path = os.path.join(base_dir, "planprompt.txt")

    target_date = "2025.05.07"
    target_datetime = "2025.05.07.22:00"

    result = {"John": {}}

    # 1. reflections
    with open(reflect_path, "r", encoding="utf-8") as f:
        reflect_data = json.load(f)
    all_reflections = reflect_data["John"]["reflections"]

    high_importance = [r for r in all_reflections if r.get("importance", 0) >= 7]
    specific_date = [r for r in all_reflections if r.get("created") == target_datetime]

    seen_keys = set()
    unique_reflections = []

    for r in high_importance + specific_date:
        key = (r["event"])
        if key not in seen_keys:
            seen_keys.add(key)
            unique_reflections.append(r)

    result["John"]["reflections"] = unique_reflections

    # 2. plans
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    if target_date in plan_data["John"]["plans"]:
        result["John"]["plans"] = {
            target_date: plan_data["John"]["plans"][target_date]
        }

    # 3. baseprompt.txt 로드
    with open(base_prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read().strip()

    # 4. JSON 병합 결과 문자열로 변환
    json_block = json.dumps(result, ensure_ascii=False, indent=2)

    # 5. base prompt + JSON을 planprompt.txt에 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_block)           
        f.write(base_prompt + "\n\n")  

    print("baseprompt + memory + plan 병합 완료 → planprompt.txt 저장됨.")

def main():
    save_combined_memory()
    try:
        with open("planprompt.txt", "r", encoding="utf-8") as file:
            prompt_text = file.read().strip()
        if prompt_text:
            get_response(prompt_text)
        else:
            print("planprompt.txt가 비어 있습니다.")
    except FileNotFoundError:
        print("planprompt.txt 파일을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()