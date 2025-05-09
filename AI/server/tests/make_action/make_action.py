import json
import time
import urllib.request
import os

API_URL = "http://localhost:11434/api/generate"  # Ollama 서버 주소 (변경 시 수정 필요)

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

    print(f"⏱ Response time: {elapsed:.2f}s")
    raw_text = raw.decode('utf-8')
    return json.loads(raw_text).get("response", "").strip()

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    base_prompt_path = os.path.join(base_dir, "action_baseprompt.txt")
    input_path = os.path.join(base_dir, "input_data.txt")

    # Load base prompt
    with open(base_prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read().strip()

    # Load input data
    with open(input_path, "r", encoding="utf-8") as f:
        input_data = f.read().strip()

    # Combine prompt
    full_prompt = f"{base_prompt}\n\n{input_data}"

    # Send to model
    print("🚀 Sending prompt to gemma3...")
    response = get_response(full_prompt)
    print("\n🧠 Response:\n", response)

if __name__ == "__main__":
    main()
