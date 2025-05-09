import urllib.request
import json
import time
import http.client

# ==============================
#  서버 호출 함수
# ==============================
def get_response(prompt: str) -> str:
    """
    prompt 문자열을 LLM 서버에 보내고,
    JSON 응답에서 'response' 필드를 꺼내 출력 후 반환합니다.
    """
    # 서버 주소 설정
    PORT = 11434
    HOST = 'localhost'
    
    # 매 요청마다 새로운 연결 생성
    conn = http.client.HTTPConnection(HOST, PORT)
    
    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "stream": False
    }
    
    # HTTP 요청 준비
    data = json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}

    # 요청-응답 시간 측정 시작
    start_time = time.time()
    conn.request('POST', '/api/generate', data, headers)
    resp = conn.getresponse()
    raw = resp.read()
    elapsed = time.time() - start_time

    # 받은 바이트를 디코딩하고 JSON 파싱
    result = json.loads(raw.decode('utf-8'))
    answer = result.get("response", "")

    # 결과 출력
    print("\n🧠 응답:")
    print(answer)
    print(f"\n⏱ 응답시간: {elapsed:.3f}초\n")

    # 연결 종료
    conn.close()

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
    try:
        # 테스트용 프롬프트
        test_prompt = """
You are the AI controller for agents in a simulation game.

AGENT DATA:
Tom: hungry, not sleepy, not lonely, at House
Visible: Kitchen located in House, Bedroom located in House, Desk located in House, Cafeteria located in Cafeteria
Can interact with: Kitchen located in House, LivingRoom located in House, Bedroom located in House, Desk located in House, Cafeteria located in Cafeteria

TASK: For each agent, determine ONE NEXT ACTION based on their current state.

ACTION OPTIONS:
- move: go to a new location
- interact: use/manipulate an object
- eat: consume food
- talk: speak to another agent
- wait: remain inactive briefly
- think: internal thought process
- idle: remain idle without taking any action
- sleep: sleep to recover energy (agent becomes inactive for a longer period)
- die: be removed from the simulation

LOCATION OPTIONS:
- house: a private residence where agents can live and rest
- cafeteria: communal dining area where agents can eat and socialize

OBJECT OPTIONS:
- Kitchen: a space equipped for cooking and food preparation
- Desk: a workspace for studying or working
- Cafeteria: meeting friend, can relieve loneliness
- LivingRoom: a common area for relaxation and social activities
- Bedroom: a private space for sleeping and personal activities

REASONING GUIDELINES:
- Explain the reasons for your actions in 100 characters or less
- Describe your thoughts and feeling
- Describe it in the first person

RESPONSE FORMAT (provide ONLY valid JSON):
{
  "agent": "agent_name",
  "action": "action_type",
  "details": {
    "location": "location_name",
    "target": "object_or_agent",
    "using": "item_if_needed",
    "message": "spoken_text_or_thought"
  },
  "reason": "reasoning_text"
}

IMPORTANT RULES:
- location must be selected ONLY from LOCATION OPTIONS (house or cafeteria)
- target must be selected ONLY from OBJECT OPTIONS (Kitchen, Desk, Cafeteria, LivingRoom, or Bedroom)
- When parsing visible and interact descriptions, split "'object' located at 'location'" format into appropriate location and target values
- IMPORTANT: Even if an object name sounds like a room (e.g., Bedroom, Kitchen), it should be treated as an object in the target field, not as a location
- location represents the broader area where the agent is (house or cafeteria), while target represents specific objects or spaces within that location
- CRITICAL: target field must ONLY contain the exact object name from OBJECT OPTIONS (e.g., "Bedroom", "Kitchen"), not the full "object located at location" format
- If you see "object located at location" in the input, extract ONLY the object part for the target field
- Provide EXACTLY ONE action per character. Respond ONLY with JSON"""
        
        print("테스트 프롬프트 전송 중...")
        get_response(test_prompt)
            
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
