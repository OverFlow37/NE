import urllib.request
import json
import time

# ==============================
#  서버 호출 함수
# ==============================
def get_response(prompt: str) -> str:
    """
    prompt 문자열을 LLM 서버에 보내고,
    JSON 응답에서 'response' 필드를 꺼내 출력 후 반환합니다.
    """
    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "stream": False  # 스트리밍 모드를 꺼서 단일 JSON 응답을 받습니다
    }
    # HTTP 요청 준비
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    # 요청-응답 시간 측정 시작
    start_time = time.time()
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
    elapsed = time.time() - start_time

    # 받은 바이트를 디코딩하고 JSON 파싱
    result = json.loads(raw.decode('utf-8'))
    answer = result.get("response", "")

    # 결과 출력
    print("\n🧠 응답:")
    print(answer)
    print(f"\n⏱ 응답시간: {elapsed:.3f}초\n")

    return answer

# ==============================
#  프롬프트 로딩 & 상태 변환 함수
# ==============================
def load_prompt(txt_path: str, json_path: str) -> str:
    """
    1) prompt.txt에서 자연어 지침을 읽고,
    2) state.json에서 에이전트 상태를 읽은 후
    3) hunger, sleepiness, loneliness 수치를 'very/not' 구문으로 바꿔
       원본 JSON의 agent['state'] 필드에 덮어쓰고,
    4) 지침 + 수정된 JSON dump를 합쳐서 반환합니다.
    """
    # 1) 지침 불러오기
    with open(txt_path, 'r', encoding='utf-8') as f:
        instruction = f.read().strip()

    # 2) 상태 JSON 불러오기
    with open(json_path, 'r', encoding='utf-8') as f:
        state_obj = json.load(f)

    # 3) 수치 → 형용사 매핑 테이블
    metric_adj = {
        "hunger": "hungry",
        "sleepiness": "sleepy",
        "loneliness": "lonely"
    }
    # 수치(level: 1~10) 를 natural language로 변환
    def describe(level: int, adj: str) -> str:
        if level <= 3:
            return f"not {adj}"
        elif level <= 6:
            return adj
        else:
            return f"very {adj}"

    # 4) agents 배열 순회하면서 state 필드를 변환
    for agent in state_obj.get("agents", []):
        st = agent.get("state", {})
        parts = []
        # hunger, sleepiness, loneliness 순서대로
        for key in ("hunger", "sleepiness", "loneliness"):
            if key in st:
                parts.append(describe(st[key], metric_adj[key]))
        # 숫자 dict 대신 자연어 문자열로 대체
        # ex: "very hungry, not sleepy, not lonely"
        agent["state"] = ", ".join(parts)

    # 5) 최종 프롬프트 조립: 지침 + JSON dump
    prompt = instruction + "\n\n" + json.dumps(state_obj, ensure_ascii=False, indent=2)
    return prompt

# ==============================
#  스크립트 진입점
# ==============================
if __name__ == "__main__":
    # 서버 주소 설정
    PORT = 11434
    HOST = 'localhost'
    API_URL = f"http://{HOST}:{PORT}/api/generate"

    # prompt.txt 와 state.json 경로를 지정
    prompt = load_prompt('prompt.txt', 'state.json')

    # 프롬프트 찍어보기
    print("===== SEND PROMPT =====")
    print(prompt)
    print("===== END PROMPT =====\n")

    # LLM 호출
    get_response(prompt)
