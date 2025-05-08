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

def extract_json_block(text: str) -> str:
    """텍스트 내에서 첫 번째 JSON 블록만 추출"""
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        raise ValueError("JSON 블록을 찾을 수 없습니다.")

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

    try:
        json_text = extract_json_block(answer)
        plan_data = json.loads(json_text)

        # sleep 존재 여부 확인
        john = plan_data.get("John", {})
        plans = john.get("plans", {})
        for date, content in plans.items():
            time_slots = content.get("time_slots", [])
            has_sleep = any(slot[0] == "sleep" for slot in time_slots)
            if not has_sleep:
                last_slot = time_slots[-1]
                last_location = last_slot[1]
                last_target = last_slot[2] if len(last_slot) > 2 else ""

                # sleep 추가
                time_slots.append(["sleep", last_location, last_target, "22:00", "06:00"])
                content["time_slots"] = time_slots
                content.setdefault("daily_plan", []).append("Sleep from 22:00 to 06:00 to recover energy.")

        answer = json.dumps(plan_data, indent=2)

    except Exception as e:
        print("⚠️ sleep 보정 중 오류 발생:", e)

    print("\n 응답:")
    print(answer)
    print(f"\n 응답시간: {elapsed:.3f}초\n")

    return answer



def save_combined_memory():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reflect_path = os.path.join(base_dir, "reflect", "reflections.json")
    plan_path = os.path.join(base_dir, "plan", "plan.json")
    base_prompt_path = os.path.join(base_dir, "baseprompt.txt")
    output_path = os.path.join(base_dir, "planprompt.txt")

    target_date = "2025.05.03"
    target_datetime = "2025.05.03.22:00"

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
        key = (r["event"], r["action"])
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